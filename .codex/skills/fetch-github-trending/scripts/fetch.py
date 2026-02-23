"""Fetch trending repositories from GitHub Trending page."""

import io
import json
import sys

# Ensure UTF-8 stdio on all platforms (Windows defaults to GBK/cp936)
for _stream in ('stdin', 'stdout', 'stderr'):
    _cur = getattr(sys, _stream)
    if hasattr(_cur, 'buffer') and _cur.encoding and _cur.encoding.lower().replace('-', '') != 'utf8':
        setattr(sys, _stream, io.TextIOWrapper(_cur.buffer, encoding='utf-8'))

import httpx
from bs4 import BeautifulSoup

TRENDING_URL = "https://github.com/trending"


def fetch_trending() -> dict:
    items = []

    with httpx.Client(timeout=10.0) as client:
        response = client.get(TRENDING_URL)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        repo_articles = soup.find_all("article", class_="Box-row", limit=25)

        for article in repo_articles:
            try:
                repo_link = article.find("h2", class_="h3").find("a")
                if not repo_link:
                    continue

                repo_full_name = repo_link.get("href", "").strip("/")
                repo_url = f"https://github.com/{repo_full_name}"

                description_tag = article.find("p", class_="col-9")
                description = description_tag.get_text(strip=True) if description_tag else ""

                language_tag = article.find("span", itemprop="programmingLanguage")
                language = language_tag.get_text(strip=True) if language_tag else "Unknown"

                stars_today = 0
                stars_today_tag = article.find("span", class_="d-inline-block float-sm-right")
                if stars_today_tag:
                    stars_text = stars_today_tag.get_text(strip=True)
                    parts = stars_text.split()
                    if parts and parts[0].replace(",", "").isdigit():
                        stars_today = int(parts[0].replace(",", ""))

                total_stars = 0
                total_stars_tag = article.find("svg", class_="octicon-star")
                if total_stars_tag and total_stars_tag.parent:
                    stars_text = total_stars_tag.parent.get_text(strip=True)
                    if stars_text.replace(",", "").isdigit():
                        total_stars = int(stars_text.replace(",", ""))

                items.append({
                    "source": "github_trending",
                    "source_id": repo_full_name,
                    "title": repo_full_name,
                    "url": repo_url,
                    "content": description,
                    "metadata": {
                        "language": language,
                        "stars_today": stars_today,
                        "total_stars": total_stars
                    },
                    "published_at": None
                })

            except Exception:
                continue

    return {"success": True, "items": items, "count": len(items), "error": ""}


if __name__ == "__main__":
    try:
        result = fetch_trending()
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"success": False, "items": [], "count": 0, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)
