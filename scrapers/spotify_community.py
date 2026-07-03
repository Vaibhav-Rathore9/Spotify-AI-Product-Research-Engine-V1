"""
Spotify Community scraper for forum posts.

Fetches live posts from the Spotify Community forum
(community.spotify.com) via their public RSS feeds
and returns them in the standardized review schema.
"""

import requests
import xml.etree.ElementTree as ET
import re
import hashlib
from html import unescape

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


def _fetch_board(board_id):
    """
    Fetch posts from a single Spotify Community board via RSS.

    Returns:
        List[dict]: Posts in the standardized schema.
    """
    url = RSS_URL_TEMPLATE.format(board_id=board_id)
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "SpotifyReviewEngine/1.0 (Research)"
        })
        resp.raise_for_status()
    except requests.RequestException:
        return []

    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError:
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

    return posts


def scrape_spotify_community(count=100):
    """
    Fetch live posts from the Spotify Community forum.

    Scrapes multiple board RSS feeds and merges results.

    Args:
        count: Maximum number of posts to return (default 100).

    Returns:
        List[dict]: Posts in the standardized schema:
            {id, source, title, text, url, date, author}
    """
    all_posts = []

    for board_id in BOARD_IDS:
        board_posts = _fetch_board(board_id)
        all_posts.extend(board_posts)

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

    return unique_posts[:count]
