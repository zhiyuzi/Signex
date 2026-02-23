"""Fetch hot topics from V2EX public API."""

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

V2EX_API_URL = "https://www.v2ex.com/api/topics/hot.json"


def fetch_hot_topics() -> dict:
    items = []

    with httpx.Client(timeout=10.0) as client:
        response = client.get(V2EX_API_URL)
        response.raise_for_status()
        topics = response.json()

        for topic in topics:
            try:
                topic_id = topic.get("id")
                title = topic.get("title", "")
                url = topic.get("url", "")
                content = topic.get("content", "")

                if content and len(content) > 500:
                    content = content[:500] + "..."

                node = topic.get("node", {})
                node_name = node.get("name", "") if isinstance(node, dict) else ""
                replies = topic.get("replies", 0)
                member = topic.get("member", {})
                member_name = member.get("username", "") if isinstance(member, dict) else ""

                created_timestamp = topic.get("created")
                published_at = None
                if created_timestamp:
                    published_at = datetime.fromtimestamp(created_timestamp, tz=timezone.utc).isoformat()

                items.append({
                    "source": "v2ex",
                    "source_id": str(topic_id),
                    "title": title,
                    "url": url,
                    "content": content,
                    "metadata": {
                        "node_name": node_name,
                        "replies": replies,
                        "member": member_name
                    },
                    "published_at": published_at
                })

            except Exception:
                continue

    return {"success": True, "items": items, "count": len(items), "error": ""}


if __name__ == "__main__":
    try:
        result = fetch_hot_topics()
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"success": False, "items": [], "count": 0, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)
