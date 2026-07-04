import json
import os
import logging
from typing import Optional
from utils.scraper_result import ScraperResult

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_filepath(source_name):
    """Generate a safe filename for the cache based on the source name."""
    safe_name = source_name.lower().replace(" ", "_")
    return os.path.join(CACHE_DIR, f"{safe_name}.json")

def save_cache(source_name, reviews):
    """Save scraped data to a JSON cache file."""
    filepath = get_cache_filepath(source_name)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(reviews, f, indent=4, ensure_ascii=False)
        logger.info(f"Successfully cached {len(reviews)} items for {source_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to save cache for {source_name}: {e}")
        return False

def load_cache(source_name):
    """Load scraped data from a JSON cache file."""
    filepath = get_cache_filepath(source_name)
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Successfully loaded {len(data)} items from cache for {source_name}")
            return data
        except Exception as e:
            logger.error(f"Failed to load cache for {source_name}: {e}")
    return []

def fetch_with_cache(source_name, scraper_fn, count=100, use_cache: bool = False) -> ScraperResult:
    """
    Fetch data using the scraper function with intelligent caching.
    
    Args:
        source_name: Name of the data source
        scraper_fn: Scraper function that returns ScraperResult
        count: Number of reviews to fetch
        use_cache: If True, try cache first; if False, always scrape fresh
        
    Returns:
        ScraperResult with caching metadata
    """
    logger.info(f"Fetching from {source_name} (use_cache={use_cache})")
    
    if use_cache:
        # Try cache first if user explicitly enabled it
        cached_data = load_cache(source_name)
        if cached_data:
            logger.info(f"Using cached data for {source_name}: {len(cached_data)} reviews")
            return ScraperResult.success_result(source_name, cached_data, used_cache=True)
    
    # Attempt fresh scraping
    try:
        result = scraper_fn(count=count)
        
        # If scraping succeeded and returned reviews, save to cache
        if result.success and result.reviews:
            save_cache(source_name, result.reviews)
            result.used_cache = False
            logger.info(f"Scraping succeeded for {source_name}: {result.review_count} reviews")
        elif not result.success:
            # Scraping failed, try to load from cache as fallback
            logger.warning(f"Scraping failed for {source_name}: {result.error}")
            cached_data = load_cache(source_name)
            if cached_data:
                logger.info(f"Falling back to cached data for {source_name}: {len(cached_data)} reviews")
                result.reviews = cached_data
                result.review_count = len(cached_data)
                result.used_cache = True
            else:
                logger.warning(f"No cached data available for {source_name}")
        
        return result
        
    except Exception as e:
        logger.exception(f"Unexpected error scraping {source_name}: {str(e)}")
        # Try to load from cache on exception
        cached_data = load_cache(source_name)
        if cached_data:
            logger.info(f"Falling back to cached data for {source_name}: {len(cached_data)} reviews")
            return ScraperResult.failure_result(
                source_name, 
                str(e), 
                used_cache=True, 
                cached_reviews=cached_data
            )
        else:
            return ScraperResult.failure_result(source_name, str(e))
