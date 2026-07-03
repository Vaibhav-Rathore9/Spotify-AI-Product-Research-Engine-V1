import os
import json
import re
import logging
from dotenv import load_dotenv

try:
    import google.generativeai as genai
except ImportError:
    genai = None

load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY and genai:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY or genai package missing. Using fallback dashboard generator.")

PROMPT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "prompts", "dashboard_prompt.txt"
)

def load_dashboard_prompt():
    """Load the dashboard prompt template from disk."""
    if os.path.exists(PROMPT_PATH):
        try:
            with open(PROMPT_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading dashboard prompt template: {e}")
    return """Analyze the following tagged reviews and output a structured dashboard JSON.
The JSON must contain discovery_barriers, recommendation_frustrations, listening_behaviors, user_segments, representative_quotes, and unmet_needs.
"""

def _mock_generate_dashboard(tagged_reviews):
    """
    Fallback deterministic dashboard generator.
    Inspects reviews to populate the six required sections.
    """
    barriers = []
    frustrations = []
    behaviors = []
    segments = []
    quotes = []
    needs = []
    
    # Counts of occurrences for categorization
    lyrics_count = 0
    shuffle_count = 0
    crash_count = 0
    ui_count = 0
    local_count = 0
    podcast_count = 0
    
    for r in tagged_reviews:
        text = r.get("text", "").lower()
        pain = r.get("pain_point", "").lower()
        
        # Aggregate counts
        if "lyrics" in text or "lyrics" in pain:
            lyrics_count += 1
        if "shuffle" in text or "shuffle" in pain:
            shuffle_count += 1
        if "crash" in text or "bug" in text or "close" in text or "crash" in pain:
            crash_count += 1
        if "ui" in text or "design" in text or "layout" in text or "ui" in pain:
            ui_count += 1
        if "local files" in text or "sync" in text or "mp3" in text or "local files" in pain:
            local_count += 1
        if "podcast" in text or "podcast" in pain:
            podcast_count += 1
            
        # Select representative quotes (up to 4)
        if len(quotes) < 4 and r.get("text") and len(r["text"]) < 200:
            quotes.append({
                "quote": r["text"],
                "source": r.get("source", "Unknown"),
                "theme": r.get("pain_point", "General Feedback")
            })
            
    # 1. Discovery Barriers
    if lyrics_count > 0:
        barriers.append({
            "barrier": "Lyrics Sync & Loading Delay",
            "count": lyrics_count,
            "examples": ["Lyrics are out of sync or take forever to load on mobile devices."]
        })
    if local_count > 0:
        barriers.append({
            "barrier": "Local Files Sync Defect",
            "count": local_count,
            "examples": ["Users cannot discover or play their local desktop MP3s on mobile over Wi-Fi."]
        })
    if not barriers:
        barriers.append({
            "barrier": "General Interface Navigational Blocks",
            "count": 1,
            "examples": ["Difficult to discover specific menu features post UI update."]
        })
        
    # 2. Recommendation Frustrations
    if shuffle_count > 0:
        frustrations.append({
            "frustration": "Smart Shuffle Intrusion",
            "count": shuffle_count,
            "details": "Smart Shuffle forces recommended songs into custom playlists instead of playing standard random order."
        })
    if podcast_count > 0:
        frustrations.append({
            "frustration": "Forced Podcast Recommendations",
            "count": podcast_count,
            "details": "Intrusive non-music content recommended on the home screen with no toggle to hide."
        })
    if not frustrations:
        frustrations.append({
            "frustration": "Redundant Music Recommendations",
            "count": 1,
            "details": "Algorithm repeats the same sets of songs in recommended queues."
        })
        
    # 3. Listening Behaviors
    behaviors.append({
        "behavior": "Custom Playlist Listening",
        "context": "Users prefer curated, specific playlist queues and dislike external algorithm modifications."
    })
    if lyrics_count > 0:
        behaviors.append({
            "behavior": "Active Lyric Sing-Along",
            "context": "Users regularly view live syncing lyrics panel while playing tracks."
        })
        
    # 4. User Segments
    if shuffle_count > 0 or ui_count > 0:
        segments.append({
            "segment": "Playlist Purist",
            "description": "Prefers listening strictly to their own custom tracks without algorithmic recommendations or UI disruptions."
        })
    if lyrics_count > 0:
        segments.append({
            "segment": "Lyrics Lovers",
            "description": "Active users who use the app primarily for karaoke-style listening and sing-alongs."
        })
    if local_count > 0:
        segments.append({
            "segment": "Local Library Collectors",
            "description": "Power users with heavy custom MP3 local audio libraries syncing to mobile."
        })
    if not segments:
        segments.append({
            "segment": "Casual Music Streamers",
            "description": "Standard users listening to general music in the background."
        })
        
    # 5. Representative Quotes (Ensure we have at least some quotes)
    if not quotes:
        quotes = [
            {"quote": "I just want standard shuffle back without recommendations.", "source": "Play Store", "theme": "Shuffle"},
            {"quote": "Lyrics have been broken for weeks, please sync them.", "source": "Reddit", "theme": "Lyrics"}
        ]
        
    # 6. Unmet Needs
    if shuffle_count > 0:
        needs.append({
            "need": "Simple Shuffle Toggle Control",
            "explanation": "A clean setting to permanently disable Smart Shuffle and enforce classic random order."
        })
    if local_count > 0:
        needs.append({
            "need": "Robust Offline Local Library Mode",
            "explanation": "Easy, direct file transfer and playback path for external media libraries."
        })
    if not needs:
        needs.append({
            "need": "Algorithmic Discovery Filters",
            "explanation": "Control sliders to adjust the discovery radius or similarity of recommended songs."
        })
        
    return {
        "discovery_barriers": barriers,
        "recommendation_frustrations": frustrations,
        "listening_behaviors": behaviors,
        "user_segments": segments,
        "representative_quotes": quotes,
        "unmet_needs": needs
    }

def generate_dashboard_data(tagged_reviews):
    """
    Generate structured dashboard sections via Gemini LLM or fallback deterministic engine.
    """
    if not tagged_reviews:
        return _mock_generate_dashboard([])

    if not GEMINI_API_KEY or not genai:
        return _mock_generate_dashboard(tagged_reviews)

    prompt_template = load_dashboard_prompt()
    
    condensed_reviews = []
    for r in tagged_reviews:
        condensed_reviews.append({
            "text": r.get("text", ""),
            "pain_point": r.get("pain_point", ""),
            "user_goal": r.get("user_goal", ""),
            "behavior": r.get("behavior", ""),
            "emotion": r.get("emotion", ""),
            "discovery_barrier": r.get("discovery_barrier", "")
        })
        
    reviews_json = json.dumps(condensed_reviews, ensure_ascii=False)
    full_prompt = f"{prompt_template}\n\nReviews:\n{reviews_json}"

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            full_prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        cleaned_text = response.text.strip()
        if cleaned_text.startswith("```"):
            cleaned_text = re.sub(r"^```(?:json)?\n", "", cleaned_text)
            cleaned_text = re.sub(r"\n```$", "", cleaned_text)
            
        parsed_json = json.loads(cleaned_text.strip())
        
        # Verify all 6 keys are present
        required_keys = [
            "discovery_barriers", "recommendation_frustrations", "listening_behaviors",
            "user_segments", "representative_quotes", "unmet_needs"
        ]
        for key in required_keys:
            if key not in parsed_json:
                parsed_json[key] = []
                
        return parsed_json
    except Exception as e:
        logger.error(f"Gemini dashboard generation error: {e}. Falling back to mock generator.")
        return _mock_generate_dashboard(tagged_reviews)
