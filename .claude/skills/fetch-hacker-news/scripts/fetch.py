"""Fetch top stories from Hacker News via Firebase API."""

import argparse
import io
import json
import sys
from datetime import datetime, timezone

# Ensure UTF-8 stdio on all platforms (Windows defaults to GBK/cp936)
for _stream in ('stdin', 'stdout', 'stderr'):
    _cur = getattr(sys, _stream)
    if hasattr(_cur, 'buffer') and _cur.encoding and _cur.encoding.lower().replace('-', '') != 'utf8':
        setattr(sys, _stream, io.TextIOWrapper(_cur.buffer, encoding='utf-8'))

import httpx

BASE_URL = "https://hacker-news.firebaseio.com/v0"


def fetch_top_stories(max_items: int = 30) -> dict:
    items = []

    with httpx.Client(timeout=10.0) as client:
        response = client.get(f"{BASE_URL}/topstories.json")
        response.raise_for_status()
        story_ids = response.json()[:max_items]

        for story_id in story_ids:
            try:
                item_response = client.get(f"{BASE_URL}/item/{story_id}.json")
                item_response.raise_for_status()
                data = item_response.json()

                if not data:
                    continue

                title = data.get("title", "")
                url = data.get("url", "")
                score = data.get("score", 0)
                descendants = data.get("descendants", 0)
                by = data.get("by", "")
                item_type = data.get("type", "")
                timestamp = data.get("time")

                published_at = None
                if timestamp:
                    published_at = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()

                items.append({
                    "source": "hacker_news",
                    "source_id": str(story_id),
                    "title": title,
                    "url": url,
                    "content": f"Score: {score}, Comments: {descendants}",
                    "metadata": {
                        "score": score,
                        "descendants": descendants,
                        "by": by,
                        "type": item_type
                    },
                    "published_at": published_at
                })

            except Exception:
                continue

    return {"success": True, "items": items, "count": len(items), "error": ""}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-items", type=int, default=30)
    args = parser.parse_args()

    try:
        result = fetch_top_stories(args.max_items)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"success": False, "items": [], "count": 0, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)
