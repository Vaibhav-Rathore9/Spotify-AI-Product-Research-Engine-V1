import os
import json
import re
import logging
from dotenv import load_dotenv

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Load environment variables
load_dotenv()

# Initialize logger
logger = logging.getLogger(__name__)

# Configure Gemini if key and library are available
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY and genai:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Gemini API configured successfully.")
else:
    logger.warning("GEMINI_API_KEY or google-generativeai package missing. Using fallback tagging engine.")

# Path to the tagging prompt template
PROMPT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "prompts", "tagging_prompt.txt"
)


def load_tagging_prompt():
    """Load the tagging prompt template from disk."""
    if os.path.exists(PROMPT_PATH):
        try:
            with open(PROMPT_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading tagging prompt template: {e}")
    # Inline default fallback prompt matching the problem statement
    return """Analyze this review.

Return ONLY JSON.

Output schema:

{
    "pain_point": "",
    "user_goal": "",
    "behavior": "",
    "emotion": "",
    "discovery_barrier": ""
}

No markdown.

No explanations.

One review at a time.
"""


def _mock_tag_review(text):
    """
    Fallback regex/keyword-based tagging engine when LLM is unavailable.
    Provides realistic Spotify-oriented tags based on review content.
    """
    text_lower = text.lower()

    # Default tags
    tags = {
        "pain_point": "General app usability or performance issues",
        "user_goal": "Listen to music and podcasts seamlessly",
        "behavior": "Streaming media content",
        "emotion": "Neutral",
        "discovery_barrier": "General playback barrier"
    }

    # Match topics
    if "lyrics" in text_lower:
        tags["pain_point"] = "Lyrics not syncing or failing to load"
        tags["user_goal"] = "View lyrics and sing along to songs"
        tags["behavior"] = "Viewing lyrics panel mid-song"
        tags["emotion"] = "Annoyed"
        tags["discovery_barrier"] = "Lyrics service sync delay"
    elif "shuffle" in text_lower or "smart shuffle" in text_lower:
        tags["pain_point"] = "Forced Smart Shuffle or poor shuffle logic"
        tags["user_goal"] = "Listen to curated playlist in standard random order"
        tags["behavior"] = "Toggling playlist shuffle"
        tags["emotion"] = "Frustrated"
        tags["discovery_barrier"] = "Recommendation algorithm override"
    elif "ui" in text_lower or "design" in text_lower or "layout" in text_lower:
        tags["pain_point"] = "Confusing layout or navigation updates"
        tags["user_goal"] = "Navigate libraries and liked songs efficiently"
        tags["behavior"] = "Browsing library navigation pages"
        tags["emotion"] = "Displeased"
        tags["discovery_barrier"] = "UI navigation layout shifts"
    elif "crash" in text_lower or "crashes" in text_lower or "closes" in text_lower or "bug" in text_lower:
        tags["pain_point"] = "App crashes or closes unexpectedly"
        tags["user_goal"] = "Ensure uninterrupted background music playback"
        tags["behavior"] = "Playing music or opening the app"
        tags["emotion"] = "Angry"
        tags["discovery_barrier"] = "Technical stability issues"
    elif "widget" in text_lower:
        tags["pain_point"] = "Widget displays blank screen or fails to resize"
        tags["user_goal"] = "Quick-control music from the home screen"
        tags["behavior"] = "Using Android/iOS home widget controls"
        tags["emotion"] = "Irritated"
        tags["discovery_barrier"] = "Widget rendering defect"
    elif "local files" in text_lower or "mp3" in text_lower or "sync" in text_lower:
        tags["pain_point"] = "Local MP3 files fail to sync or play on mobile"
        tags["user_goal"] = "Play local custom audio library on mobile devices"
        tags["behavior"] = "Syncing local desktop files to mobile over Wi-Fi"
        tags["emotion"] = "Disappointed"
        tags["discovery_barrier"] = "Local files Wi-Fi sync barrier"
    elif "podcast" in text_lower or "podcasts" in text_lower:
        tags["pain_point"] = "Intrusive podcast recommendations on home screen"
        tags["user_goal"] = "Customize home screen to show music only"
        tags["behavior"] = "Scrolling home screen feed"
        tags["emotion"] = "Annoyed"
        tags["discovery_barrier"] = "Forced non-musical content recommendations"

    # Refine emotion based on keywords
    if any(w in text_lower for w in ["hate", "worst", "garbage", "trash", "terrible", "useless"]):
        tags["emotion"] = "Angry"
    elif any(w in text_lower for w in ["love", "best", "great", "awesome", "perfect", "good"]):
        tags["emotion"] = "Happy"
    elif any(w in text_lower for w in ["annoying", "annoyed", "bother", "sucks", "disappoint"]):
        tags["emotion"] = "Annoyed"

    return tags


def tag_review(review_text):
    """
    Process a single review text via LLM (Gemini) to output structured JSON tags.
    Falls back to a keyword-based tagger if Gemini is unconfigured or fails.
    """
    if not review_text or not review_text.strip():
        return {
            "pain_point": "N/A",
            "user_goal": "N/A",
            "behavior": "N/A",
            "emotion": "N/A",
            "discovery_barrier": "N/A"
        }

    # Fall back if no API key is set or library is missing
    if not GEMINI_API_KEY or not genai:
        return _mock_tag_review(review_text)

    prompt_template = load_tagging_prompt()
    full_prompt = f"{prompt_template}\n\nReview:\n\"{review_text}\""

    try:
        # Use gemini-1.5-flash for fast text generation
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            full_prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Clean response and parse JSON
        cleaned_text = response.text.strip()
        # Remove potential markdown fences just in case
        if cleaned_text.startswith("```"):
            cleaned_text = re.sub(r"^```(?:json)?\n", "", cleaned_text)
            cleaned_text = re.sub(r"\n```$", "", cleaned_text)
        
        parsed_json = json.loads(cleaned_text.strip())
        
        # Ensure all required fields are present
        required_keys = ["pain_point", "user_goal", "behavior", "emotion", "discovery_barrier"]
        for key in required_keys:
            if key not in parsed_json:
                parsed_json[key] = "N/A"
                
        return parsed_json
    except Exception as e:
        logger.error(f"Gemini tagging error: {e}. Falling back to mock tagger.")
        return _mock_tag_review(review_text)


def tag_reviews_batch(reviews):
    """
    Process a list of reviews in batch.
    Adds tagging keys directly to the review objects.
    
    Args:
        reviews (List[dict]): List of review dicts.
        
    Returns:
        List[dict]: The updated list of reviews containing tagged attributes.
    """
    tagged_reviews = []
    for r in reviews:
        review_text = r.get("text", "")
        # Fallback to title if text is empty (e.g. some Reddit posts have no body text)
        if not review_text.strip() and r.get("title"):
            review_text = r.get("title")
            
        tags = tag_review(review_text)
        
        # Merge tags into review dictionary
        tagged_review = r.copy()
        tagged_review.update(tags)
        tagged_reviews.append(tagged_review)
        
    return tagged_reviews
