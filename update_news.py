import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

FEEDS = [
    "https://feeds.bbci.co.uk/hindi/rss.xml",
    "https://feeds.feedburner.com/ndtvkhabar-latest"
]

def clean(text):
    if not text:
        return ""
    text = re.sub(r"<!\[CDATA\[|\]\]>", "", text)
    text = re.sub(r"<[^>]+>", " ", text)

    for a, b in {
        "&amp;": "&",
        "&quot;": '"',
        "&#39;": "'",
        "&lt;": "<",
        "&gt;": ">"
    }.items():
        text = text.replace(a, b)

    return " ".join(text.split())


def get_image(item):
    for child in item:
        tag = child.tag.lower()

        if "thumbnail" in tag or "content" in tag:
            url = child.attrib.get("url")
            if url:
                return url

        if "enclosure" in tag:
            url = child.attrib.get("url")
            if url:
                return url

    description = item.findtext("description") or ""

    match = re.search(
        r'<img[^>]+src=["\']([^"\']+)',
        description,
        re.I
    )

    return match.group(1) if match else ""


def fetch_feed(url):
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:
            data = response.read()

        root = ET.fromstring(data)
        results = []

        for item in root.findall(".//item"):

            title = clean(item.findtext("title"))
            link = clean(item.findtext("link"))
            description = clean(
                item.findtext("description")
            )
            pub_date = clean(
                item.findtext("pubDate")
            )
            source = clean(
                item.findtext("source")
            )
            image = get_image(item)

            if not title or not link:
                continue

            timestamp = 0

            try:
                timestamp = parsedate_to_datetime(
                    pub_date
                ).timestamp()
            except Exception:
                pass

            results.append({
                "title": title,
                "description": description[:300],
                "link": link,
                "source": source,
                "image": image,
                "timestamp": timestamp,
                "pubDate": pub_date
            })

        return results

    except Exception as error:
        print("Feed error:", url)
        print(error)
        return []


all_news = []

for feed in FEEDS:
    all_news.extend(fetch_feed(feed))


all_news.sort(
    key=lambda x: x["timestamp"],
    reverse=True
)


# Duplicate headlines हटाना
unique = []
seen = set()

for item in all_news:

    key = re.sub(
        r"[^a-zA-Z0-9\u0900-\u097F]",
        "",
        item["title"].lower()
    )

    if key in seen:
        continue

    seen.add(key)
    unique.append(item)


# आज उपलब्ध latest news का pool
news_pool = unique[:20]


output = {
    "updated": datetime.now(
        timezone.utc
    ).isoformat(),
    "news": news_pool
}


with open(
    "news.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        output,
        file,
        ensure_ascii=False,
        indent=2
    )


print("NEWS UPDATED:", len(news_pool))

for i, item in enumerate(news_pool, 1):
    print(i, item["title"])
