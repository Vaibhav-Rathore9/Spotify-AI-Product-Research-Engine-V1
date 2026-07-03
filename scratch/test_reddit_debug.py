import requests
import xml.etree.ElementTree as ET
import traceback

def test_reddit_debug():
    url = "https://www.reddit.com/r/spotify/new.rss"
    headers = {
        "User-Agent": "desktop:spotify-review-discovery-engine:v1.0 (by /u/antigravity_bot)"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        print("Status Code:", resp.status_code)
        resp.raise_for_status()
        
        # print first 500 chars of text
        print("Text preview:", resp.text[:500])
        
        root = ET.fromstring(resp.text)
        print("XML Parsed successfully.")
        
        NS = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", NS)
        print("Entries count:", len(entries))
        
    except Exception as e:
        print("Error encountered:")
        traceback.print_exc()

if __name__ == "__main__":
    test_reddit_debug()
