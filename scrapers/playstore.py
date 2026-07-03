"""
Google Play Store scraper for Spotify reviews.

Fetches live user reviews from the Google Play Store
and returns them in the standardized review schema.
"""

from google_play_scraper import reviews, Sort

SPOTIFY_APP_ID = "com.spotify.music"


def scrape_playstore(count=100):
    """
    Fetch live Spotify reviews from Google Play Store.

    Args:
        count: Number of reviews to fetch (default 100).

    Returns:
        List[dict]: Reviews in the standardized schema:
            {id, source, title, text, url, date, author}
    """
    raw_reviews, _ = reviews(
        SPOTIFY_APP_ID,
        lang="en",
        country="us",
        sort=Sort.NEWEST,
        count=count,
    )

    standardized = []
    for r in raw_reviews:
        standardized.append({
            "id": r.get("reviewId", ""),
            "source": "Google Play Store",
            "title": f"Rating: {r.get('score', 'N/A')}/5",
            "text": r.get("content", ""),
            "url": f"https://play.google.com/store/apps/details?id={SPOTIFY_APP_ID}&reviewId={r.get('reviewId', '')}",
            "date": str(r.get("at", "")),
            "author": r.get("userName", "Anonymous"),
        })

    return standardized
