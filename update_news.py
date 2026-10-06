import json
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

FEEDS = {
    "hindi": [
        "https://feeds.bbci.co.uk/hindi/rss.xml",
        "https://feeds.feedburner.com/ndtvkhabar-latest",
    ],
    "english": [
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://www.indiatoday.in/rss/1206578",
    ],
}

def clean(text):
    if not text:
        return ""
    return " ".join(text.replace("<![CDATA[", "").replace("]]>", "").split())

def get_news(url, limit=8):
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            data = response.read()

        root = ET.fromstring(data)
        items = []

        for item in root.findall(".//item")[:limit]:
            title = clean(item.findtext("title"))
            link = clean(item.findtext("link"))
            description = clean(item.findtext("description"))
            pub_date = clean(item.findtext("pubDate"))

            if not title or not link:
                continue

            items.append({
                "title": title,
                "description": description[:220],
                "link": link,
                "pubDate": pub_date
            })

        return items

    except Exception as e:
        print("Feed error:", url, e)
        return []

news = {
    "updated": datetime.now(timezone.utc).isoformat(),
    "hindi": [],
    "english": []
}

for url in FEEDS["hindi"]:
    news["hindi"].extend(get_news(url))

for url in FEEDS["english"]:
    news["english"].extend(get_news(url))

# Duplicate headlines हटाना
def unique(items):
    seen = set()
    result = []

    for item in items:
        key = item["title"].lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)

    return result[:10]

news["hindi"] = unique(news["hindi"])
news["english"] = unique(news["english"])

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(news, f, ensure_ascii=False, indent=2)

print("News updated successfully.")
print("Hindi:", len(news["hindi"]))
print("English:", len(news["english"]))
