import json
import os
import logging

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_filepath(source_name):
    """Generate a safe filename for the cache based on the source name."""
    safe_name = source_name.lower().replace(" ", "_")
    return os.path.join(CACHE_DIR, f"{safe_name}.json")

def save_cache(source_name, data):
    """Save scraped data to a JSON cache file."""
    filepath = get_cache_filepath(source_name)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logging.info(f"Successfully cached {len(data)} items for {source_name}")
    except Exception as e:
        logging.error(f"Failed to save cache for {source_name}: {e}")

def load_cache(source_name):
    """Load scraped data from a JSON cache file."""
    filepath = get_cache_filepath(source_name)
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            logging.info(f"Successfully loaded {len(data)} items from cache for {source_name}")
            return data
        except Exception as e:
            logging.error(f"Failed to load cache for {source_name}: {e}")
    return []

def fetch_with_cache(source_name, scraper_fn, count=100):
    """
    Attempt to fetch data using the scraper function.
    If successful, overwrite the cache.
    If it fails, load and return the cached data.
    """
    try:
        data = scraper_fn(count=count)
        if data:
            save_cache(source_name, data)
            return data
        else:
            raise ValueError("Scraper returned empty data.")
    except Exception as e:
        logging.warning(f"Scraping failed for {source_name} ({e}). Falling back to cache.")
        return load_cache(source_name)
