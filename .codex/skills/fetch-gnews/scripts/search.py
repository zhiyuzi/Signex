"""Search news via GNews API."""

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

GNEWS_API_URL = "https://gnews.io/api/v4/search"


def search(queries: list[str], max_results: int = 10, language: str = "en") -> dict:
    api_key = os.getenv("GNEWS_API_KEY")
    if not api_key:
        return {"success": False, "items": [], "count": 0, "error": "GNEWS_API_KEY not set"}

    unique_urls: dict[str, dict] = {}

    with httpx.Client(timeout=15.0) as client:
        for query in queries:
            try:
                response = client.get(GNEWS_API_URL, params={
                    "q": query,
                    "max": min(max_results, 10),
                    "lang": language,
                    "token": api_key
                })
                response.raise_for_status()
                data = response.json()

                for article in data.get("articles", []):
                    url = article.get("url", "")
                    if not url or url in unique_urls:
                        continue

                    source_id = hashlib.md5(url.encode()).hexdigest()[:12]
                    source_info = article.get("source", {})
                    unique_urls[url] = {
                        "source": "gnews",
                        "source_id": source_id,
                        "title": article.get("title", ""),
                        "url": url,
                        "content": article.get("description", "") or "",
                        "metadata": {
                            "source_name": source_info.get("name", ""),
                            "source_url": source_info.get("url", ""),
                            "language": language,
                            "country": None
                        },
                        "published_at": article.get("publishedAt")
                    }

            except Exception:
                continue

    items = list(unique_urls.values())
    return {"success": True, "items": items, "count": len(items), "error": ""}


if __name__ == "__main__":
    try:
        input_data = json.load(sys.stdin)
        queries = input_data.get("queries", [])
        max_results = input_data.get("max_results", 10)
        language = input_data.get("language", "en")

        if not queries:
            print(json.dumps({"success": True, "items": [], "count": 0, "error": ""}, ensure_ascii=False))
        else:
            result = search(queries, max_results, language)
            print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"success": False, "items": [], "count": 0, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)
