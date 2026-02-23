"""Fetch posts from Reddit via public JSON API."""

import io
import json
import sys

# Ensure UTF-8 stdio on all platforms (Windows defaults to GBK/cp936)
for _stream in ('stdin', 'stdout', 'stderr'):
    _cur = getattr(sys, _stream)
    if hasattr(_cur, 'buffer') and _cur.encoding and _cur.encoding.lower().replace('-', '') != 'utf8':
        setattr(sys, _stream, io.TextIOWrapper(_cur.buffer, encoding='utf-8'))

import httpx
from datetime import datetime, timezone

USER_AGENT = "Signex/1.0 (personal research tool)"
BASE_URL = "https://www.reddit.com"


def fetch_subreddits(subreddits: list[str], sort: str = "hot", limit: int = 25) -> dict:
    items = []

    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        for sub in subreddits:
            try:
                url = f"{BASE_URL}/r/{sub}/{sort}.json"
                response = client.get(
                    url,
                    params={"limit": limit, "raw_json": 1},
                    headers={"User-Agent": USER_AGENT},
                )
                response.raise_for_status()
                data = response.json()

                for child in data.get("data", {}).get("children", []):
                    post = child.get("data", {})
                    if not post:
                        continue

                    selftext = post.get("selftext", "")
                    if len(selftext) > 300:
                        selftext = selftext[:300]

                    created_utc = post.get("created_utc")
                    published_at = None
                    if created_utc:
                        published_at = datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat()

                    items.append({
                        "source": "reddit",
                        "source_id": post.get("id", ""),
                        "title": post.get("title", ""),
                        "url": post.get("url", ""),
                        "content": selftext,
                        "metadata": {
                            "subreddit": post.get("subreddit", sub),
                            "score": post.get("score", 0),
                            "num_comments": post.get("num_comments", 0),
                            "author": post.get("author", ""),
                            "upvote_ratio": post.get("upvote_ratio", 0),
                            "permalink": post.get("permalink", ""),
                        },
                        "published_at": published_at,
                    })

            except Exception:
                continue

    return {"success": True, "items": items, "count": len(items), "error": ""}


def search_reddit(query: str, subreddit: str = "all", sort: str = "relevance", time: str = "week", limit: int = 25) -> dict:
    items = []

    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        try:
            url = f"{BASE_URL}/r/{subreddit}/search.json"
            response = client.get(
                url,
                params={
                    "q": query,
                    "restrict_sr": 1,
                    "sort": sort,
                    "t": time,
                    "limit": limit,
                    "raw_json": 1,
                },
                headers={"User-Agent": USER_AGENT},
            )
            response.raise_for_status()
            data = response.json()

            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                if not post:
                    continue

                selftext = post.get("selftext", "")
                if len(selftext) > 300:
                    selftext = selftext[:300]

                created_utc = post.get("created_utc")
                published_at = None
                if created_utc:
                    published_at = datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat()

                items.append({
                    "source": "reddit",
                    "source_id": post.get("id", ""),
                    "title": post.get("title", ""),
                    "url": post.get("url", ""),
                    "content": selftext,
                    "metadata": {
                        "subreddit": post.get("subreddit", subreddit),
                        "score": post.get("score", 0),
                        "num_comments": post.get("num_comments", 0),
                        "author": post.get("author", ""),
                        "upvote_ratio": post.get("upvote_ratio", 0),
                        "permalink": post.get("permalink", ""),
                    },
                    "published_at": published_at,
                })

        except Exception as e:
            return {"success": False, "items": items, "count": len(items), "error": str(e)}

    return {"success": True, "items": items, "count": len(items), "error": ""}


if __name__ == "__main__":
    try:
        input_data = json.load(sys.stdin)

        if "search" in input_data:
            result = search_reddit(
                query=input_data["search"],
                subreddit=input_data.get("subreddit", "all"),
                sort=input_data.get("sort", "relevance"),
                time=input_data.get("time", "week"),
                limit=input_data.get("limit", 25),
            )
        elif "subreddits" in input_data:
            result = fetch_subreddits(
                subreddits=input_data["subreddits"],
                sort=input_data.get("sort", "hot"),
                limit=input_data.get("limit", 25),
            )
        else:
            result = {"success": True, "items": [], "count": 0, "error": ""}

        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"success": False, "items": [], "count": 0, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)
