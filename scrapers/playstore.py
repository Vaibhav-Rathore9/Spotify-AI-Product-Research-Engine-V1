"""
Google Play Store scraper for Spotify reviews.

Fetches live user reviews from the Google Play Store
and returns them in the standardized review schema.
"""

import logging
from google_play_scraper import reviews, Sort
from utils.scraper_result import ScraperResult

SPOTIFY_APP_ID = "com.spotify.music"

logger = logging.getLogger(__name__)


def scrape_playstore(count=100) -> ScraperResult:
    """
    Fetch live Spotify reviews from Google Play Store.

    Args:
        count: Number of reviews to fetch (default 100).

    Returns:
        ScraperResult: Standardized result object with reviews and metadata.
    """
    logger.info(f"Starting Google Play Store scraper for {count} reviews")
    
    try:
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

        logger.info(f"Successfully scraped {len(standardized)} reviews from Google Play Store")
        return ScraperResult.success_result("Google Play Store", standardized)
        
    except Exception as e:
        logger.exception(f"Google Play Store scraping failed: {str(e)}")
        return ScraperResult.failure_result("Google Play Store", str(e))
