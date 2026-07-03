import requests

url = "https://www.reddit.com/r/spotify/new.rss"
# Custom unique user agent identifying our engine
headers = {
    "User-Agent": "desktop:spotify-review-discovery-engine:v1.0 (by /u/antigravity_bot)"
}

try:
    resp = requests.get(url, headers=headers, timeout=15)
    print("Status:", resp.status_code)
    print("Snippet:", resp.text[:200])
except Exception as e:
    print("Error:", e)
