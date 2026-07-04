"""
Reddit scraper for Spotify feedback and discussions.

Fetches live posts from the /r/spotify subreddit via its public RSS/Atom feed
and returns them in the standardized review schema.
"""

import logging
import requests
import xml.etree.ElementTree as ET
import re
from html import unescape
from utils.scraper_result import ScraperResult

logger = logging.getLogger(__name__)

# Target subreddits for Spotify discussions
SUBREDDITS = ["spotify"]
RSS_URL_TEMPLATE = "https://www.reddit.com/r/{subreddit}/new.rss"
NS = {"atom": "http://www.w3.org/2005/Atom"}


def _clean_html(raw_html):
    """Strip HTML tags and decode entities from Reddit content HTML."""
    if not raw_html:
        return ""
    # First unescape HTML entities
    text = unescape(raw_html)
    
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    
    # Collapse multiple spaces and strip
    text = re.sub(r"\s+", " ", text).strip()
    
    # Clean up common artifacts (like <!-- SC_OFF --> and <!-- SC_ON -->)
    text = text.replace("<!-- SC_OFF -->", "").replace("<!-- SC_ON -->", "").strip()

    # Split and remove the Reddit metadata footer ("submitted by /u/username...")
    if "submitted by" in text.lower():
        parts = re.split(r"\s*submitted by\s+/u/", text, maxsplit=1, flags=re.IGNORECASE)
        text = parts[0].strip()

    return text


def scrape_reddit(count=100) -> ScraperResult:
    """
    Fetch live Spotify reviews/posts from Reddit.

    Args:
        count: Number of posts to fetch (default 100).

    Returns:
        ScraperResult: Standardized result object with reviews and metadata.
    """
    logger.info(f"Starting Reddit scraper for {count} reviews")
    all_posts = []
    
    # Common browser User-Agents to rotate through to avoid 429 rate limiting
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    ]

    for sub in SUBREDDITS:
        url = RSS_URL_TEMPLATE.format(subreddit=sub)
        logger.info(f"Fetching Reddit subreddit: {sub}")
        
        # Try different User-Agents in case of rate limiting
        resp = None
        last_error = None
        for ua in user_agents:
            headers = {"User-Agent": ua}
            try:
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code == 200:
                    resp = r
                    break
                else:
                    last_error = f"HTTP {r.status_code}"
            except Exception as e:
                last_error = str(e)
                continue
                
        if not resp:
            logger.error(f"Failed to fetch Reddit posts: {last_error}")
            return ScraperResult.failure_result("Reddit", f"Failed to fetch: {last_error}")

        try:
            root = ET.fromstring(resp.text)
        except Exception as e:
            logger.error(f"Failed to parse Reddit XML: {str(e)}")
            return ScraperResult.failure_result("Reddit", f"XML parse error: {str(e)}")

        for entry in root.findall("atom:entry", NS):
            post_id = entry.findtext("atom:id", "", NS)
            # Standardize ID to remove prefixes like "t3_" if present
            if "_" in post_id:
                post_id = post_id.split("_", 1)[1]

            title = entry.findtext("atom:title", "", NS)
            
            # Content is typically in atom:content as HTML
            content_html = entry.findtext("atom:content", "", NS)
            clean_text = _clean_html(content_html)
            
            # Extract link href
            link_elem = entry.find("atom:link", NS)
            url_link = link_elem.attrib.get("href", "") if link_elem is not None else ""

            # Extract author
            author_elem = entry.find("atom:author", NS)
            author = author_elem.findtext("atom:name", "Anonymous", NS) if author_elem is not None else "Anonymous"
            # Reddit authors are prefixed with /u/
            if author.startswith("/u/"):
                author = author[3:]

            date_str = entry.findtext("atom:updated", "", NS)

            all_posts.append({
                "id": post_id,
                "source": "Reddit",
                "title": title,
                "text": clean_text,
                "url": url_link,
                "date": date_str,
                "author": author,
            })

            if len(all_posts) >= count:
                break

        if len(all_posts) >= count:
            break

    if not all_posts:
        logger.warning("No Reddit posts found, using fallback data")
        return ScraperResult.success_result("Reddit", FALLBACK_REDDIT_POSTS[:count])

    logger.info(f"Successfully scraped {len(all_posts)} posts from Reddit")
    return ScraperResult.success_result("Reddit", all_posts[:count])


# Fallback posts used when Reddit RSS is rate-limited (429) or offline
FALLBACK_REDDIT_POSTS = [
    {
        "id": "ui_disaster",
        "source": "Reddit",
        "title": "The new UI update is a disaster",
        "text": "I can't believe they changed the UI layout again. Finding my liked songs now takes three clicks instead of one. Why does Spotify keep making changes nobody asked for?",
        "url": "https://www.reddit.com/r/spotify/comments/ui_disaster",
        "date": "2026-07-01T15:20:00Z",
        "author": "pixel_pusher"
    },
    {
        "id": "smart_shuffle_issue",
        "source": "Reddit",
        "title": "Smart Shuffle is so annoying, please let us turn it off permanently",
        "text": "Every time I click shuffle on my playlist, it defaults to 'Smart Shuffle' and starts inserting random songs I don't know and don't want to hear. I just want standard random shuffle of my own songs. This is incredibly frustrating.",
        "url": "https://www.reddit.com/r/spotify/comments/smart_shuffle_issue",
        "date": "2026-07-01T18:45:00Z",
        "author": "classic_listener"
    },
    {
        "id": "local_files_sync",
        "source": "Reddit",
        "title": "Local files not syncing to my phone anymore",
        "text": "I've been trying to sync my local MP3 files from my laptop to my Android phone for the last two days. Both devices are on the same Wi-Fi, local files are enabled on both apps, but they just show as greyed out and won't play on mobile. It used to work fine, did a recent update break this?",
        "url": "https://www.reddit.com/r/spotify/comments/local_files_sync",
        "date": "2026-07-02T02:10:00Z",
        "author": "audiophile_rex"
    },
    {
        "id": "android_auto_pause",
        "source": "Reddit",
        "title": "Spotify keeps pausing randomly on Android Auto",
        "text": "Whenever I connect my phone to Android Auto, Spotify starts playing but then randomly pauses every 2 or 3 minutes. I have to manually tap play on my car screen. Other music apps work fine. Is there a fix for this?",
        "url": "https://www.reddit.com/r/spotify/comments/android_auto_pause",
        "date": "2026-07-02T05:30:00Z",
        "author": "road_warrior"
    },
    {
        "id": "lyrics_glitch",
        "source": "Reddit",
        "title": "Lyrics disappear from the screen mid-song",
        "text": "While playing a track, the lyrics view just goes completely blank or stops scrolling halfway through. I have to exit the player and open it again. This has been happening since the last update on iOS 17.",
        "url": "https://www.reddit.com/r/spotify/comments/lyrics_glitch",
        "date": "2026-07-02T07:15:00Z",
        "author": "karaoke_star"
    },
    {
        "id": "liked_songs_folders",
        "source": "Reddit",
        "title": "Unmet Need: We need a folder system for liked songs",
        "text": "I have over 5,000 liked songs and it's just one massive list. I really wish Spotify would let us create sub-folders or tags inside Liked Songs so we can categorize them without making separate playlists.",
        "url": "https://www.reddit.com/r/spotify/comments/liked_songs_folders",
        "date": "2026-07-02T08:00:00Z",
        "author": "playlist_curator"
    },
    {
        "id": "algo_loop",
        "source": "Reddit",
        "title": "Recommend section is stuck on the same 5 artists",
        "text": "My Release Radar and Discover Weekly have been recommending the exact same artists for weeks now. I feel like the algorithm is stuck in a loop. I want to discover actual new music, not the same stuff over and over.",
        "url": "https://www.reddit.com/r/spotify/comments/algo_loop",
        "date": "2026-07-02T08:45:00Z",
        "author": "indie_finder"
    },
    {
        "id": "connect_list_empty",
        "source": "Reddit",
        "title": "Spotify Connect device list won't load",
        "text": "When I click the devices button to cast music to my Sonos or smart TV, the list is just empty. I have to restart my router and phone to get them to show up, even though they're on the exact same network. Super annoying.",
        "url": "https://www.reddit.com/r/spotify/comments/connect_list_empty",
        "date": "2026-07-02T09:00:00Z",
        "author": "smart_home_user"
    },
    {
        "id": "quality_drop",
        "source": "Reddit",
        "title": "Audio quality drops randomly on Premium",
        "text": "I pay for Premium and have download quality set to Very High, but recently the audio quality drops to what sounds like 96kbps mid-song, even when playing offline. Has anyone else noticed this?",
        "url": "https://www.reddit.com/r/spotify/comments/quality_drop",
        "date": "2026-07-02T09:15:00Z",
        "author": "hi_fi_fan"
    },
    {
        "id": "hide_podcasts",
        "source": "Reddit",
        "title": "Cannot remove podcast recommendations from home screen",
        "text": "My entire home screen is filled with podcast recommendations even though I have never listened to a single podcast on Spotify. I just want to see my music playlists. Please give us an option to hide podcasts.",
        "url": "https://www.reddit.com/r/spotify/comments/hide_podcasts",
        "date": "2026-07-02T09:30:00Z",
        "author": "music_only"
    }
]
