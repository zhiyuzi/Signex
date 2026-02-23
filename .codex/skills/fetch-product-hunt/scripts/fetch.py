"""Fetch featured posts from Product Hunt via GraphQL API."""

import argparse
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

GRAPHQL_URL = "https://api.producthunt.com/v2/api/graphql"

POSTS_QUERY = """
query GetPosts($first: Int, $featured: Boolean, $topic: String, $postedAfter: DateTime) {
  posts(first: $first, featured: $featured, topic: $topic, postedAfter: $postedAfter) {
    edges {
      node {
        id
        name
        tagline
        slug
        votesCount
        commentsCount
        url
        website
        featuredAt
        topics {
          edges {
            node {
              name
            }
          }
        }
      }
    }
  }
}
"""


def fetch(limit: int = 20, featured: bool = False, topic: str | None = None, after: str | None = None) -> dict:
    token = os.getenv("PRODUCTHUNT_ACCESS_TOKEN")
    if not token:
        return {"success": False, "items": [], "count": 0, "error": "PRODUCTHUNT_ACCESS_TOKEN not set"}

    variables: dict = {"first": limit}
    if featured:
        variables["featured"] = True
    if topic:
        variables["topic"] = topic
    if after:
        variables["postedAfter"] = f"{after}T00:00:00Z"

    items = []

    with httpx.Client(timeout=15.0) as client:
        try:
            response = client.post(
                GRAPHQL_URL,
                json={"query": POSTS_QUERY, "variables": variables},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

            edges = data.get("data", {}).get("posts", {}).get("edges", [])
            for edge in edges:
                node = edge.get("node", {})
                if not node:
                    continue

                topic_names = [
                    t["node"]["name"]
                    for t in node.get("topics", {}).get("edges", [])
                    if t.get("node", {}).get("name")
                ]

                items.append({
                    "source": "product_hunt",
                    "source_id": str(node.get("id", "")),
                    "title": node.get("name", ""),
                    "url": node.get("url", ""),
                    "content": node.get("tagline", ""),
                    "metadata": {
                        "tagline": node.get("tagline", ""),
                        "votes_count": node.get("votesCount", 0),
                        "comments_count": node.get("commentsCount", 0),
                        "topics": topic_names,
                        "featured_at": node.get("featuredAt"),
                        "website": node.get("website", ""),
                    },
                    "published_at": node.get("featuredAt"),
                })

        except Exception as e:
            return {"success": False, "items": items, "count": len(items), "error": str(e)}

    return {"success": True, "items": items, "count": len(items), "error": ""}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--featured", action="store_true")
    parser.add_argument("--topic", type=str, default=None)
    parser.add_argument("--after", type=str, default=None)
    args = parser.parse_args()

    try:
        result = fetch(args.limit, args.featured, args.topic, args.after)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"success": False, "items": [], "count": 0, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)
