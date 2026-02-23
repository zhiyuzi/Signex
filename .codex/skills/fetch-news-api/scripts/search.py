"""Search news articles via NewsAPI.org."""

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

NEWS_API_URL = "https://newsapi.org/v2/everything"


def search(queries: list[str], days: int = 7, language: str = "en", sort_by: str = "relevancy") -> dict:
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return {"success": False, "items": [], "count": 0, "error": "NEWS_API_KEY not set"}

    from datetime import datetime, timedelta, timezone
    from_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    unique_urls: dict[str, dict] = {}

    with httpx.Client(timeout=15.0) as client:
        for query in queries:
            try:
                response = client.get(NEWS_API_URL, params={
                    "q": query,
                    "from": from_date,
                    "language": language,
                    "sortBy": sort_by,
                    "pageSize": 20,
                    "apiKey": api_key
                })
                response.raise_for_status()
                data = response.json()

                for article in data.get("articles", []):
                    url = article.get("url", "")
                    if not url or url in unique_urls:
                        continue

                    source_id = hashlib.md5(url.encode()).hexdigest()[:12]
                    unique_urls[url] = {
                        "source": "news_api",
                        "source_id": source_id,
                        "title": article.get("title", ""),
                        "url": url,
                        "content": article.get("description", "") or "",
                        "metadata": {
                            "source_name": article.get("source", {}).get("name", ""),
                            "author": article.get("author", ""),
                            "relevancy_score": None
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
        days = input_data.get("days", 7)
        language = input_data.get("language", "en")
        sort_by = input_data.get("sort_by", "relevancy")

        if not queries:
            print(json.dumps({"success": True, "items": [], "count": 0, "error": ""}, ensure_ascii=False))
        else:
            result = search(queries, days, language, sort_by)
            print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"success": False, "items": [], "count": 0, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)
