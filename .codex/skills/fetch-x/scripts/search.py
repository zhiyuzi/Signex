"""Search recent tweets via X/Twitter API v2."""

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

X_SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"


def search(queries: list[str], max_results: int = 10, min_likes: int = 0, min_retweets: int = 0) -> dict:
    bearer_token = os.getenv("X_BEARER_TOKEN")
    if not bearer_token:
        return {"success": False, "items": [], "count": 0, "error": "X_BEARER_TOKEN not set"}

    seen_ids: set[str] = set()
    items = []
    errors = []

    with httpx.Client(timeout=15.0) as client:
        for query in queries:
            try:
                # Build query with filters
                q_parts = [query, "-is:retweet"]
                if min_likes > 0:
                    q_parts.append(f"min_faves:{min_likes}")
                if min_retweets > 0:
                    q_parts.append(f"min_retweets:{min_retweets}")

                response = client.get(X_SEARCH_URL, params={
                    "query": " ".join(q_parts),
                    "max_results": min(max(max_results, 10), 10),
                    "tweet.fields": "created_at,public_metrics,lang,author_id",
                    "expansions": "author_id",
                    "user.fields": "username"
                }, headers={
                    "Authorization": f"Bearer {bearer_token}"
                })
                if response.status_code != 200:
                    detail = response.json().get("detail", response.text[:200])
                    errors.append(f"HTTP {response.status_code}: {detail}")
                    continue
                data = response.json()

                # Build author lookup
                authors = {}
                for user in data.get("includes", {}).get("users", []):
                    authors[user["id"]] = user.get("username", "")

                for tweet in data.get("data", []):
                    tweet_id = tweet.get("id", "")
                    if not tweet_id or tweet_id in seen_ids:
                        continue
                    seen_ids.add(tweet_id)

                    metrics = tweet.get("public_metrics", {})
                    items.append({
                        "source": "x_twitter",
                        "source_id": tweet_id,
                        "title": "",
                        "url": f"https://x.com/i/status/{tweet_id}",
                        "content": tweet.get("text", ""),
                        "metadata": {
                            "author_username": authors.get(tweet.get("author_id", ""), ""),
                            "retweet_count": metrics.get("retweet_count", 0),
                            "like_count": metrics.get("like_count", 0),
                            "reply_count": metrics.get("reply_count", 0),
                            "lang": tweet.get("lang", "")
                        },
                        "published_at": tweet.get("created_at")
                    })

            except Exception:
                continue

    error_msg = "; ".join(errors) if errors else ""
    return {"success": len(errors) == 0 or len(items) > 0, "items": items, "count": len(items), "error": error_msg}


if __name__ == "__main__":
    try:
        input_data = json.load(sys.stdin)
        queries = input_data.get("queries", [])
        max_results = input_data.get("max_results", 10)
        min_likes = input_data.get("min_likes", 0)
        min_retweets = input_data.get("min_retweets", 0)

        if not queries:
            print(json.dumps({"success": True, "items": [], "count": 0, "error": ""}, ensure_ascii=False))
        else:
            result = search(queries, max_results, min_likes, min_retweets)
            print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"success": False, "items": [], "count": 0, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)
