"""Web search via Tavily API."""

import hashlib
import io
import json
import os
import sys

# Ensure UTF-8 stdio on all platforms (Windows defaults to GBK/cp936)
for _stream in ('stdin', 'stdout', 'stderr'):
    _cur = getattr(sys, _stream)
    if hasattr(_cur, 'buffer') and _cur.encoding and _cur.encoding.lower().replace('-', '') != 'utf8':
        setattr(sys, _stream, io.TextIOWrapper(_cur.buffer, encoding='utf-8'))

import httpx
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_URL = "https://api.tavily.com/search"


def search(queries: list[str], days: int = 7) -> dict:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {"success": False, "items": [], "count": 0, "error": "TAVILY_API_KEY not set"}

    unique_results: dict[str, tuple[dict, str]] = {}

    with httpx.Client(timeout=15.0) as client:
        for query in queries:
            try:
                response = client.post(TAVILY_API_URL, json={
                    "api_key": api_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": 10,
                    "include_answer": False,
                    "days": days
                })
                response.raise_for_status()
                data = response.json()

                for result in data.get("results", []):
                    url = result.get("url", "")
                    if not url:
                        continue

                    score = result.get("score", 0.0)
                    if url in unique_results:
                        existing_score = unique_results[url][0].get("score", 0.0)
                        if score <= existing_score:
                            continue

                    unique_results[url] = (result, query)

            except Exception:
                continue

    items = []
    for url, (result, query) in unique_results.items():
        source_id = hashlib.md5(url.encode()).hexdigest()[:12]
        items.append({
            "source": "web_search",
            "source_id": source_id,
            "title": result.get("title", ""),
            "url": url,
            "content": result.get("content", ""),
            "metadata": {
                "relevance_score": float(result.get("score", 0.0)),
                "query": query
            },
            "published_at": None
        })

    return {"success": True, "items": items, "count": len(items), "error": ""}


if __name__ == "__main__":
    try:
        input_data = json.load(sys.stdin)
        queries = input_data.get("queries", [])
        days = input_data.get("days", 7)

        if not queries:
            print(json.dumps({"success": True, "items": [], "count": 0, "error": ""}, ensure_ascii=False))
        else:
            result = search(queries, days)
            print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"success": False, "items": [], "count": 0, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)
