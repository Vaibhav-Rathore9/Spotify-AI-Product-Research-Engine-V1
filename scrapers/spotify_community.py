"""
Spotify Community scraper for forum posts.

Fetches live posts from the Spotify Community forum
(community.spotify.com) via their public RSS feeds
and returns them in the standardized review schema.
"""

import logging
import xml.etree.ElementTree as ET
import re
import hashlib
import time
from html import unescape
from utils.scraper_result import ScraperResult

try:
    from curl_cffi import requests as http_requests
    _HTTP_SESSION_CLASS = "curl_cffi"
except ImportError:
    import requests as http_requests
    _HTTP_SESSION_CLASS = "requests"

logger = logging.getLogger(__name__)

# Board IDs mapped to readable names — covers the main Help categories
BOARD_IDS = [
    "spotifyandroid",
    "spotifyiOS",
    "desktop_windows",
    "desktop_mac",
    "desktop_linux",
    "spotifyaccountrelated",
    "Subscriptions",
    "yourlibrary",
    "content",
]

RSS_URL_TEMPLATE = (
    "https://community.spotify.com/spotify/rss/board?board.id={board_id}"
)

# XML namespaces used in the RSS feed
NS = {"dc": "http://purl.org/dc/elements/1.1/"}


def _clean_html(raw_html):
    """Strip HTML tags and decode entities from RSS description."""
    # First unescape HTML entities
    text = unescape(raw_html)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _generate_id(link):
    """Generate a stable short ID from the post URL."""
    return hashlib.md5(link.encode()).hexdigest()[:16]


def _fetch_board(board_id, session=None):
    """
    Fetch posts from a single Spotify Community board via RSS.

    Args:
        board_id: The board identifier (e.g. 'spotifyandroid').
        session: Optional pre-created HTTP session for connection reuse.

    Returns:
        List[dict]: Posts in the standardized schema.
    """
    url = RSS_URL_TEMPLATE.format(board_id=board_id)
    logger.info(f"Fetching Spotify Community board: {board_id}")

    # Create a session if none provided
    if session is None:
        if _HTTP_SESSION_CLASS == "curl_cffi":
            session = http_requests.Session(impersonate="chrome")
        else:
            session = http_requests.Session()
    
    try:
        resp = session.get(url, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"HTTP error fetching board {board_id}: {str(e)}")
        return []

    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError as e:
        logger.error(f"XML parse error for board {board_id}: {str(e)}")
        return []

    posts = []
    for item in root.findall(".//item"):
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        description = item.findtext("description", "")
        pub_date = item.findtext("pubDate", "")
        author = item.findtext("dc:creator", "Anonymous", NS)

        # Clean the description HTML to plain text
        clean_text = _clean_html(description)

        posts.append({
            "id": _generate_id(link),
            "source": "Spotify Community",
            "title": title,
            "text": clean_text,
            "url": link,
            "date": pub_date,
            "author": author,
        })

    logger.info(f"Fetched {len(posts)} posts from board {board_id}")
    return posts


def scrape_spotify_community(count=100) -> ScraperResult:
    """
    Fetch live posts from the Spotify Community forum.

    Scrapes multiple board RSS feeds and merges results.

    Args:
        count: Maximum number of posts to return (default 100).

    Returns:
        ScraperResult: Standardized result object with reviews and metadata.
    """
    logger.info(f"Starting Spotify Community scraper for {count} reviews")
    all_posts = []
    errors = []

    # Create one session for all board requests (reuses TCP connections)
    if _HTTP_SESSION_CLASS == "curl_cffi":
        session = http_requests.Session(impersonate="chrome")
    else:
        session = http_requests.Session()

    for board_id in BOARD_IDS:
        board_posts = _fetch_board(board_id, session=session)
        if not board_posts:
            errors.append(f"Board {board_id} returned no posts")
        all_posts.extend(board_posts)

        # Small delay between boards to be respectful
        time.sleep(0.5)

        # Stop early if we already have enough
        if len(all_posts) >= count:
            break

    # Deduplicate by ID (in case a post appears in multiple feeds)
    seen = set()
    unique_posts = []
    for post in all_posts:
        if post["id"] not in seen:
            seen.add(post["id"])
            unique_posts.append(post)

    final_posts = unique_posts[:count]
    
    if not final_posts:
        error_msg = "; ".join(errors[:3]) if errors else "All boards returned no posts"
        logger.warning(f"Spotify Community scraping returned 0 posts: {error_msg}")
        return ScraperResult.failure_result("Spotify Community", error_msg)
    
    logger.info(f"Successfully scraped {len(final_posts)} posts from Spotify Community")
    return ScraperResult.success_result("Spotify Community", final_posts)
