import requests
import time

url = "https://www.reddit.com/r/spotify/new.rss"
uas = [
    "reddit-rss-scraper-v1.0-test",
    "spotify-insight-gen-bot-123",
    "my-test-app-for-spotify-1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
]

for ua in uas:
    print(f"Testing UA: '{ua}'")
    headers = {"User-Agent": ua}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print("Status:", resp.status_code)
        if resp.status_code == 200:
            print("Success! Snippet:", resp.text[:100])
            break
    except Exception as e:
        print("Error:", e)
    time.sleep(2)
