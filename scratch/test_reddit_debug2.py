import requests
import xml.etree.ElementTree as ET
import traceback
from scrapers.reddit import _clean_html

url = "https://www.reddit.com/r/spotify/new.rss"
user_agents = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]

resp = None
for ua in user_agents:
    headers = {"User-Agent": ua}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print(f"UA: {ua[:30]}... Status: {r.status_code}")
        if r.status_code == 200:
            resp = r
            break
    except Exception as e:
        print("Fetch exception:", e)

if resp:
    try:
        root = ET.fromstring(resp.text)
        NS = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", NS)
        print("Found entries in debug:", len(entries))
        for entry in entries[:2]:
            post_id = entry.findtext("atom:id", "", NS)
            print("Post ID:", post_id)
            title = entry.findtext("atom:title", "", NS)
            print("Title:", title)
    except Exception as e:
        traceback.print_exc()
else:
    print("No successful response fetched.")
