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
    logger.warning("GEMINI_API_KEY or genai package missing. Using fallback clustering engine.")

PROMPT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "prompts", "clustering_prompt.txt"
)

def load_clustering_prompt():
    """Load the clustering prompt template from disk."""
    if os.path.exists(PROMPT_PATH):
        try:
            with open(PROMPT_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading clustering prompt template: {e}")
    return """Analyze the following tagged reviews and cluster them into common overarching themes.
Return ONLY JSON representing a list of themes with keys: theme, frequency, supporting_quotes, summary, root_cause, opportunities, expected_impact, confidence_score.
"""

def _mock_cluster_reviews(tagged_reviews):
    """
    Fallback deterministic clustering engine.
    Groups reviews based on the 'pain_point' or 'emotion' tags.
    """
    themes_map = {}
    
    # Pre-defined opportunity mappings for mock themes
    mock_opps = {
        "Lyrics Sync & Loading Issues": {
            "root_cause": "The backend sync service experiencing lag and rendering bottlenecks on cellular connections.",
            "opportunities": [
                "Pre-fetch lyrics during song buffering on the player layer",
                "Integrate local cached offline lyrics support for top 100 downloaded songs",
                "Add a 'report sync bug' button directly inside the lyrics interface"
            ],
            "expected_impact": "Improve satisfaction among lyrics-lovers and karaoke-style listeners.",
            "confidence_score": "88%"
        },
        "Smart Shuffle Frustrations": {
            "root_cause": "Recommendation algorithm overrides standard user settings, forcing un-saved track inserts.",
            "opportunities": [
                "Implement a strict toggle slider controlling the density of recommended songs inside shuffle mode",
                "Introduce a 'Classic Shuffle Only' setting in general settings",
                "Provide a quick dislike/remove button next to recommended tracks in play queue"
            ],
            "expected_impact": "Eliminate frustration for playlist purists wanting classic play control.",
            "confidence_score": "94%"
        },
        "App Stability & Crashes": {
            "root_cause": "Memory leaks during background audio service operations, specifically on Android background resource allocation rules.",
            "opportunities": [
                "Re-architect Android background audio lifecycles with strict memory usage constraints",
                "Implement automated background state crash dumps for offline debugging",
                "Optimize resource cleanup cycles between podcast and music players"
            ],
            "expected_impact": "Decrease crash rates by 40% and prevent playback interruptions.",
            "confidence_score": "92%"
        },
        "Confusing UI Updates": {
            "root_cause": "Redesigned library architecture shifts menu items, creating navigation friction and muscle-memory disruption.",
            "opportunities": [
                "Introduce contextual tooltips guiding users to new folder and playlists menu nodes",
                "Provide custom navbar customization support to rearrange libraries",
                "Allow users to toggle a 'Simple Library Interface' layout"
            ],
            "expected_impact": "Reduce initial navigation confusion and ease design transition friction.",
            "confidence_score": "85%"
        },
        "Local Files Sync Failure": {
            "root_cause": "Firewall and protocol blocks when desktop and mobile devices try to sync libraries over local Wi-Fi nodes.",
            "opportunities": [
                "Allow direct cable transfer imports on mobile client libraries",
                "Implement cloud-cached metadata matching to match local tracks directly to Spotify database",
                "Build a diagnostic sync checking screen explaining firewall steps clearly"
            ],
            "expected_impact": "Solve library collection gaps for power collectors and collectors of rare custom audio.",
            "confidence_score": "90%"
        },
        "General Playback & Usability": {
            "root_cause": "Network latency and variable cell coverage impacting network socket buffering.",
            "opportunities": [
                "Increase default playback socket buffer cache sizes",
                "Add dynamic low-bitrate mode trigger when cell reception drops below 2 bars",
                "Enhance offline state detection to switch to cached songs seamlessly"
            ],
            "expected_impact": "Reduce initial buffering stalls and buffer wait times.",
            "confidence_score": "80%"
        }
    }
    
    for r in tagged_reviews:
        pain = r.get("pain_point", "General usability issue")
        if "lyrics" in pain.lower():
            t_key = "Lyrics Sync & Loading Issues"
        elif "shuffle" in pain.lower():
            t_key = "Smart Shuffle Frustrations"
        elif "crash" in pain.lower() or "unstable" in pain.lower():
            t_key = "App Stability & Crashes"
        elif "ui" in pain.lower() or "layout" in pain.lower():
            t_key = "Confusing UI Updates"
        elif "local files" in pain.lower():
            t_key = "Local Files Sync Failure"
        else:
            t_key = "General Playback & Usability"
            
        if t_key not in themes_map:
            meta = mock_opps[t_key]
            themes_map[t_key] = {
                "theme": t_key,
                "frequency": 0,
                "supporting_quotes": [],
                "summary": f"Users are experiencing ongoing issues related to {t_key.lower()}.",
                "root_cause": meta["root_cause"],
                "opportunities": meta["opportunities"],
                "expected_impact": meta["expected_impact"],
                "confidence_score": meta["confidence_score"]
            }
            
        themes_map[t_key]["frequency"] += 1
        
        # Add up to 3 supporting quotes
        if len(themes_map[t_key]["supporting_quotes"]) < 3 and r.get("text"):
            quote = r["text"]
            if len(quote) > 100:
                quote = quote[:97] + "..."
            themes_map[t_key]["supporting_quotes"].append(quote)

    # Convert map to list and sort by frequency descending
    result = list(themes_map.values())
    result.sort(key=lambda x: x["frequency"], reverse=True)
    return result


def cluster_reviews(tagged_reviews):
    """
    Process a list of tagged reviews via LLM (Gemini) to group them into themes.
    Falls back to a heuristic clusterer if Gemini is unconfigured or fails.
    """
    if not tagged_reviews:
        return []

    if not GEMINI_API_KEY or not genai:
        return _mock_cluster_reviews(tagged_reviews)

    prompt_template = load_clustering_prompt()
    
    # Condense reviews into a compact JSON string to save tokens
    condensed_reviews = []
    for r in tagged_reviews:
        condensed_reviews.append({
            "text": r.get("text", ""),
            "pain_point": r.get("pain_point", ""),
            "emotion": r.get("emotion", "")
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
        
        # Ensure it returns a list
        if not isinstance(parsed_json, list):
            logger.error("Gemini returned a dict instead of list. Wrapping in list.")
            parsed_json = [parsed_json]
            
        return parsed_json
    except Exception as e:
        logger.error(f"Gemini clustering error: {e}. Falling back to mock clusterer.")
        return _mock_cluster_reviews(tagged_reviews)
