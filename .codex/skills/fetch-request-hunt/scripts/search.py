"""Search feature requests via RequestHunt API."""

import hashlib
import io
import json
import os
import sys
from datetime import datetime, timezone

# Ensure UTF-8 stdio on all platforms (Windows defaults to GBK/cp936)
for _stream in ('stdin', 'stdout', 'stderr'):
    _cur = getattr(sys, _stream)
    if hasattr(_cur, 'buffer') and _cur.encoding and _cur.encoding.lower().replace('-', '') != 'utf8':
        setattr(sys, _stream, io.TextIOWrapper(_cur.buffer, encoding='utf-8'))

import httpx
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://requesthunt.com/api/v1"


def search(queries: list[str], limit: int = 20, expand: bool = False) -> dict:
    api_key = os.getenv("REQUESTHUNT_API_KEY")
    if not api_key:
        return {"success": False, "items": [], "count": 0, "error": "REQUESTHUNT_API_KEY not set"}

    unique_results: dict[str, dict] = {}

    with httpx.Client(timeout=15.0) as client:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        for query in queries:
            try:
                response = client.post(
                    f"{API_BASE}/requests/search",
                    json={"query": query, "limit": limit, "expand": expand},
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                # API returns {"data": {"results": [...]}} nested structure
                if isinstance(data, list):
                    results = data
                elif isinstance(data.get("data"), dict):
                    results = data["data"].get("results", [])
                else:
                    results = data.get("results", data.get("data", []))

                for item in results:
                    source_url = item.get("sourceUrl", item.get("url", ""))
                    if not source_url:
                        continue

                    item_id = item.get("_id", item.get("id", hashlib.md5(source_url.encode()).hexdigest()[:12]))
                    key = str(item_id)

                    if key in unique_results:
                        continue

                    description = item.get("description", item.get("content", ""))
                    if len(description) > 500:
                        description = description[:500]

                    # Convert epoch ms to ISO 8601
                    created_at = item.get("createdAt", item.get("originalCreatedAt", item.get("publishedAt")))
                    published_at = None
                    if isinstance(created_at, (int, float)) and created_at > 1e12:
                        published_at = datetime.fromtimestamp(created_at / 1000, tz=timezone.utc).isoformat()
                    elif isinstance(created_at, str):
                        published_at = created_at

                    unique_results[key] = {
                        "source": "request_hunt",
                        "source_id": key,
                        "title": item.get("title", item.get("name", "")),
                        "url": source_url,
                        "content": description,
                        "metadata": {
                            "source_platform": item.get("sourcePlatform", item.get("source", "")),
                            "votes": item.get("votes", item.get("upvotes", 0)),
                            "comment_count": item.get("commentCount", item.get("comments", 0)),
                            "topic": item.get("topic", ""),
                            "author_name": item.get("authorName", item.get("author", "")),
                            "author_handle": item.get("authorHandle", ""),
                            "relevance_score": item.get("relevanceScore", item.get("score", 0)),
                        },
                        "published_at": published_at,
                    }

            except Exception:
                continue

    items = list(unique_results.values())
    return {"success": True, "items": items, "count": len(items), "error": ""}


if __name__ == "__main__":
    try:
        input_data = json.load(sys.stdin)
        queries = input_data.get("queries", [])
        limit = input_data.get("limit", 20)
        expand = input_data.get("expand", False)

        if not queries:
            print(json.dumps({"success": True, "items": [], "count": 0, "error": ""}, ensure_ascii=False))
        else:
            result = search(queries, limit, expand)
            print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"success": False, "items": [], "count": 0, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)
