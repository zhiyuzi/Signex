"""Web search via Brave Search API."""

import hashlib
import io
import json
import os
import re
import sys

# Ensure UTF-8 stdio on all platforms (Windows defaults to GBK/cp936)
for _stream in ('stdin', 'stdout', 'stderr'):
    _cur = getattr(sys, _stream)
    if hasattr(_cur, 'buffer') and _cur.encoding and _cur.encoding.lower().replace('-', '') != 'utf8':
        setattr(sys, _stream, io.TextIOWrapper(_cur.buffer, encoding='utf-8'))

import httpx
from dotenv import load_dotenv

load_dotenv()

BRAVE_API_URL = "https://api.search.brave.com/res/v1/web/search"
MAX_COUNT = 10  # Hard cap: $5/1000 requests, keep usage lean


def _strip_html(text: str) -> str:
    """Remove HTML tags (e.g. <strong>) from Brave description snippets."""
    return re.sub(r"<[^>]+>", "", text) if text else ""


def search(queries: list[str], count: int = 10) -> dict:
    api_key = os.getenv("BRAVE_API_KEY")
    if not api_key:
        return {"success": False, "items": [], "count": 0, "error": "BRAVE_API_KEY not set"}

    unique_results: dict[str, tuple[dict, str]] = {}

    with httpx.Client(timeout=15.0) as client:
        for query in queries:
            try:
                response = client.get(
                    BRAVE_API_URL,
                    params={"q": query, "count": min(count, MAX_COUNT)},
                    headers={"X-Subscription-Token": api_key},
                )
                response.raise_for_status()
                data = response.json()

                for result in data.get("web", {}).get("results", []):
                    url = result.get("url", "")
                    if not url:
                        continue

                    if url in unique_results:
                        continue

                    unique_results[url] = (result, query)

            except Exception:
                continue

    items = []
    for url, (result, query) in unique_results.items():
        source_id = hashlib.md5(url.encode()).hexdigest()[:12]
        items.append({
            "source": "brave_search",
            "source_id": source_id,
            "title": result.get("title", ""),
            "url": url,
            "content": _strip_html(result.get("description", "")),
            "metadata": {
                "query": query
            },
            "published_at": None,
        })

    return {"success": True, "items": items, "count": len(items), "error": ""}


if __name__ == "__main__":
    try:
        input_data = json.load(sys.stdin)
        queries = input_data.get("queries", [])
        count = input_data.get("count", 10)

        if not queries:
            print(json.dumps({"success": True, "items": [], "count": 0, "error": ""}, ensure_ascii=False))
        else:
            result = search(queries, count)
            print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"success": False, "items": [], "count": 0, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)
