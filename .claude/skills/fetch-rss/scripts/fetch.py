"""Fetch entries from RSS/Atom feeds."""

import hashlib
import io
import json
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# Ensure UTF-8 stdio on all platforms (Windows defaults to GBK/cp936)
for _stream in ('stdin', 'stdout', 'stderr'):
    _cur = getattr(sys, _stream)
    if hasattr(_cur, 'buffer') and _cur.encoding and _cur.encoding.lower().replace('-', '') != 'utf8':
        setattr(sys, _stream, io.TextIOWrapper(_cur.buffer, encoding='utf-8'))

import feedparser
import httpx

def parse_published(entry) -> str | None:
    """Extract ISO 8601 published date from a feed entry."""
    # Try published_parsed first (struct_time)
    if entry.get("published_parsed"):
        try:
            from calendar import timegm
            ts = timegm(entry.published_parsed)
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        except Exception:
            pass
    # Try updated_parsed
    if entry.get("updated_parsed"):
        try:
            from calendar import timegm
            ts = timegm(entry.updated_parsed)
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        except Exception:
            pass
    # Try raw published string
    if entry.get("published"):
        try:
            dt = parsedate_to_datetime(entry.published)
            return dt.isoformat()
        except Exception:
            pass
    return None


def fetch(feeds: list[str], max_per_feed: int = 20) -> dict:
    items = []
    failed_feeds = []

    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        for feed_url in feeds:
            try:
                response = client.get(feed_url, headers={"User-Agent": "Signex/1.0 RSS Reader"})
                response.raise_for_status()
                content = response.text

                parsed = feedparser.parse(content)
                feed_title = parsed.feed.get("title", feed_url)

                for entry in parsed.entries[:max_per_feed]:
                    link = entry.get("link", "")
                    if not link:
                        continue

                    source_id = hashlib.md5(link.encode()).hexdigest()[:12]
                    title = entry.get("title", "")
                    summary = entry.get("summary", entry.get("description", ""))
                    author = entry.get("author", "")
                    published_at = parse_published(entry)

                    items.append({
                        "source": "rss",
                        "source_id": source_id,
                        "title": title,
                        "url": link,
                        "content": summary[:500] if summary else "",
                        "metadata": {
                            "feed_url": feed_url,
                            "feed_title": feed_title,
                            "author": author,
                        },
                        "published_at": published_at,
                    })

            except Exception as e:
                failed_feeds.append(f"{feed_url}: {e}")
                continue

    error = "; ".join(failed_feeds) if failed_feeds else ""
    return {"success": True, "items": items, "count": len(items), "error": error}


if __name__ == "__main__":
    try:
        input_data = json.load(sys.stdin)
        feeds = input_data.get("feeds", [])
        max_per_feed = input_data.get("max_per_feed", 20)

        if not feeds:
            print(json.dumps({"success": True, "items": [], "count": 0, "error": ""}, ensure_ascii=False))
        else:
            result = fetch(feeds, max_per_feed)
            print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"success": False, "items": [], "count": 0, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)
