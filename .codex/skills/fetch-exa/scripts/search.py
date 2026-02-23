"""Semantic search via Exa AI SDK."""

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

from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from exa_py import Exa

load_dotenv()


def search(
    queries: list[str],
    num_results: int = 10,
    days: int = 7,
    category: str | None = None,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
) -> dict:
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        return {"success": False, "items": [], "count": 0, "error": "EXA_API_KEY not set"}

    exa = Exa(api_key)
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Dedup by URL, keep highest score
    unique: dict[str, tuple] = {}  # url -> (result, query)

    for query in queries:
        try:
            kwargs: dict = {
                "query": query,
                "num_results": num_results,
                "type": "auto",
                "start_published_date": start_date,
                "highlights": {"num_sentences": 5},
                "text": {"max_characters": 1000},
            }
            if category:
                kwargs["category"] = category
            if include_domains:
                kwargs["include_domains"] = include_domains
            if exclude_domains:
                kwargs["exclude_domains"] = exclude_domains

            response = exa.search_and_contents(**kwargs)

            for result in response.results:
                url = result.url or ""
                if not url:
                    continue
                score = result.score or 0.0
                if url in unique and (unique[url][0].score or 0.0) >= score:
                    continue
                unique[url] = (result, query)

        except Exception:
            continue

    items = []
    for url, (result, query) in unique.items():
        source_id = hashlib.md5(url.encode()).hexdigest()[:12]
        highlights = result.highlights if hasattr(result, "highlights") and result.highlights else []
        text = result.text if hasattr(result, "text") and result.text else ""
        # Prefer highlights for token-efficient content; fall back to text
        content = "\n".join(highlights) if highlights else text

        items.append({
            "source": "exa_search",
            "source_id": source_id,
            "title": result.title or "",
            "url": url,
            "content": content,
            "metadata": {
                "relevance_score": float(result.score or 0.0),
                "query": query,
                "published_date": result.published_date,
                "highlights": highlights,
            },
            "published_at": result.published_date,
        })

    return {"success": True, "items": items, "count": len(items), "error": ""}


if __name__ == "__main__":
    try:
        input_data = json.load(sys.stdin)
        queries = input_data.get("queries", [])
        num_results = input_data.get("num_results", 10)
        days = input_data.get("days", 7)
        category = input_data.get("category")
        include_domains = input_data.get("include_domains")
        exclude_domains = input_data.get("exclude_domains")

        if not queries:
            print(json.dumps({"success": True, "items": [], "count": 0, "error": ""}, ensure_ascii=False))
        else:
            result = search(queries, num_results, days, category, include_domains, exclude_domains)
            print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"success": False, "items": [], "count": 0, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)
