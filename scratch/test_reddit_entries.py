import requests
import xml.etree.ElementTree as ET

url = "https://www.reddit.com/r/spotify/new.rss"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
NS = {"atom": "http://www.w3.org/2005/Atom"}

try:
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    entries = root.findall("atom:entry", NS)
    print("Entries count:", len(entries))
except Exception as e:
    print("Error:", e)
