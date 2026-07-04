"""
Reddit scraper for Spotify feedback and discussions.

Fetches live posts from the /r/spotify subreddit via its public RSS/Atom feed
and returns them in the standardized review schema.
"""

import json
import logging
import xml.etree.ElementTree as ET
import re
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

# Target subreddits for Spotify discussions
SUBREDDITS = ["spotify"]
RSS_URL_TEMPLATE = "https://www.reddit.com/r/{subreddit}/new.rss"
JSON_URL_TEMPLATE = "https://www.reddit.com/r/{subreddit}/new.json?limit=100"
TOP_JSON_URL = "https://www.reddit.com/r/{subreddit}/top.json?limit=100&t=month"
NS = {"atom": "http://www.w3.org/2005/Atom"}

# Reddit's recommended User-Agent for bots (not browser UA — Reddit respects this)
REDDIT_BOT_UA = "SpotifyProductResearch/1.0 (product research; by /u/research-bot)"


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


def _make_request(url, timeout=15):
    """
    Make an HTTP request with the best available method.
    Uses curl_cffi with browser impersonation if available, otherwise
    plain requests with Reddit's recommended bot User-Agent.
    """
    if _HTTP_SESSION_CLASS == "curl_cffi":
        session = http_requests.Session(impersonate="chrome")
        return session.get(url, timeout=timeout)
    else:
        headers = {"User-Agent": REDDIT_BOT_UA}
        return http_requests.get(url, headers=headers, timeout=timeout)


def _fetch_rss_posts(url, seen_ids):
    """Fetch posts from a Reddit RSS/Atom feed URL."""
    resp = _make_request(url)
    if resp.status_code != 200:
        return [], resp.status_code

    try:
        root = ET.fromstring(resp.text)
    except Exception as e:
        logger.error(f"Failed to parse Reddit XML from {url}: {e}")
        return [], resp.status_code

    posts = []
    for entry in root.findall("atom:entry", NS):
        post_id = entry.findtext("atom:id", "", NS)
        if "_" in post_id:
            post_id = post_id.split("_", 1)[1]
        if post_id in seen_ids:
            continue
        seen_ids.add(post_id)

        title = entry.findtext("atom:title", "", NS)
        content_html = entry.findtext("atom:content", "", NS)
        clean_text = _clean_html(content_html)

        link_elem = entry.find("atom:link", NS)
        url_link = link_elem.attrib.get("href", "") if link_elem is not None else ""

        author_elem = entry.find("atom:author", NS)
        author = author_elem.findtext("atom:name", "Anonymous", NS) if author_elem is not None else "Anonymous"
        if author.startswith("/u/"):
            author = author[3:]

        date_str = entry.findtext("atom:updated", "", NS)

        posts.append({
            "id": post_id,
            "source": "Reddit",
            "title": title,
            "text": clean_text,
            "url": url_link,
            "date": date_str,
            "author": author,
        })

    return posts, resp.status_code


def _fetch_json_posts(url, seen_ids):
    """Fetch posts from a Reddit JSON API endpoint."""
    resp = _make_request(url)
    if resp.status_code != 200:
        return [], resp.status_code

    try:
        data = resp.json()
    except Exception as e:
        logger.error(f"Failed to parse Reddit JSON from {url}: {e}")
        return [], resp.status_code

    children = data.get("data", {}).get("children", [])
    posts = []
    for child in children:
        post_data = child.get("data", {})
        post_id = post_data.get("id", "")
        if not post_id or post_id in seen_ids:
            continue
        seen_ids.add(post_id)

        title = post_data.get("title", "")
        selftext = post_data.get("selftext", "")
        author = post_data.get("author", "Anonymous")
        permalink = post_data.get("permalink", "")
        url_link = f"https://www.reddit.com{permalink}" if permalink else ""
        created_utc = post_data.get("created_utc", "")

        # Convert UTC timestamp to ISO format
        date_str = ""
        if created_utc:
            from datetime import datetime, timezone
            date_str = datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat()

        posts.append({
            "id": post_id,
            "source": "Reddit",
            "title": title,
            "text": selftext if selftext else _clean_html(post_data.get("media_embed", {}).get("content", "")),
            "url": url_link,
            "date": date_str,
            "author": author,
        })

    return posts, resp.status_code


def scrape_reddit(count=100) -> ScraperResult:
    """
    Fetch live Spotify reviews/posts from Reddit.

    Tries multiple endpoints (RSS + JSON API) with retry + exponential
    backoff to handle rate limits. Falls back through endpoints if one fails.

    Args:
        count: Number of posts to fetch (default 100).

    Returns:
        ScraperResult: Standardized result object with reviews and metadata.
    """
    logger.info(f"Starting Reddit scraper for {count} reviews")

    all_posts = []
    seen_ids = set()
    errors = []

    # Define endpoints to try in order: JSON API first (more data), then RSS
    json_urls = [
        JSON_URL_TEMPLATE.format(subreddit="spotify"),
        TOP_JSON_URL.format(subreddit="spotify"),
    ]
    rss_urls = [
        "https://www.reddit.com/r/spotify/new/.rss",
        "https://www.reddit.com/r/spotify/.rss",
        "https://www.reddit.com/r/spotify/top/.rss?t=month",
    ]

    # Try JSON API first (returns up to 100 posts per request)
    for url in json_urls:
        if len(all_posts) >= count:
            break
        for attempt in range(3):
            try:
                posts, status = _fetch_json_posts(url, seen_ids)
                if status == 200 and posts:
                    all_posts.extend(posts)
                    logger.info(f"Fetched {len(posts)} posts from JSON API: {url}")
                    break
                elif status == 429:
                    wait = (2 ** attempt) * 5  # 5s, 10s, 20s
                    logger.warning(f"Reddit rate-limited (429) on attempt {attempt+1}, waiting {wait}s")
                    time.sleep(wait)
                else:
                    logger.warning(f"Reddit JSON returned HTTP {status} for {url}")
                    errors.append(f"JSON {url}: HTTP {status}")
                    break
            except Exception as e:
                logger.warning(f"Reddit JSON error on attempt {attempt+1}: {e}")
                time.sleep(2 ** attempt)
        time.sleep(1)

    # If JSON API failed, fall back to RSS feeds
    if not all_posts:
        logger.info("JSON API returned no data, trying RSS feeds")
        for url in rss_urls:
            if len(all_posts) >= count:
                break
            for attempt in range(3):
                try:
                    posts, status = _fetch_rss_posts(url, seen_ids)
                    if status == 200 and posts:
                        all_posts.extend(posts)
                        logger.info(f"Fetched {len(posts)} posts from RSS: {url}")
                        break
                    elif status == 429:
                        wait = (2 ** attempt) * 5
                        logger.warning(f"Reddit rate-limited (429) on attempt {attempt+1}, waiting {wait}s")
                        time.sleep(wait)
                    else:
                        logger.warning(f"Reddit RSS returned HTTP {status} for {url}")
                        errors.append(f"RSS {url}: HTTP {status}")
                        break
                except Exception as e:
                    logger.warning(f"Reddit RSS error on attempt {attempt+1}: {e}")
                    time.sleep(2 ** attempt)
            time.sleep(2)

    if not all_posts:
        error_msg = "; ".join(errors[:3]) if errors else "All endpoints returned no data"
        logger.warning(f"No Reddit posts found: {error_msg}")
        return ScraperResult.failure_result("Reddit", error_msg)

    logger.info(f"Successfully scraped {len(all_posts)} total posts from Reddit")
    return ScraperResult.success_result("Reddit", all_posts[:count])
