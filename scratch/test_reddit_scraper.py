from scrapers.reddit import scrape_reddit

def test_scraper():
    print("Fetching Reddit posts...")
    results = scrape_reddit(count=5)
    print(f"Fetched {len(results)} posts.")
    for i, r in enumerate(results, 1):
        print(f"\n--- Post {i} ---")
        print("ID:", r["id"])
        print("Source:", r["source"])
        print("Title:", r["title"])
        print("Author:", r["author"])
        print("Date:", r["date"])
        print("URL:", r["url"])
        print("Text snippet:", r["text"][:150])

if __name__ == "__main__":
    test_scraper()
