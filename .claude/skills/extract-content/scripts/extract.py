"""Extract article content from URLs."""

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


def extract_with_firecrawl(url: str, app) -> dict | None:
    """Use Firecrawl SDK for LLM-ready Markdown extraction."""
    try:
        result = app.scrape(url, formats=["markdown"])
        content = result.markdown or ""
        title = result.metadata.title if result.metadata and hasattr(result.metadata, "title") and result.metadata.title else ""
        return {
            "url": url,
            "title": title,
            "content": content,
            "word_count": len(content.split()),
            "extractor": "firecrawl",
        }
    except Exception:
        return None


def extract_with_bs4(url: str, client: httpx.Client) -> dict:
    """Fallback: extract with BeautifulSoup."""
    from bs4 import BeautifulSoup

    response = client.get(url, headers={
        "User-Agent": "Signex/1.0 (personal research tool)"
    }, follow_redirects=True)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup.find_all(["nav", "footer", "sidebar", "script", "style", "aside", "header"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    main = soup.find("main") or soup.find("article") or soup.find("div", class_="content") or soup.body
    content = main.get_text(separator="\n", strip=True) if main else ""

    return {
        "url": url,
        "title": title,
        "content": content,
        "word_count": len(content.split()),
    }


def extract(urls: list[str]) -> dict:
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
    app = None
    if firecrawl_key:
        from firecrawl import Firecrawl
        app = Firecrawl(api_key=firecrawl_key)

    results = []
    with httpx.Client(timeout=20.0) as client:
        for url in urls:
            try:
                result = None
                if app:
                    result = extract_with_firecrawl(url, app)
                if result is None:
                    result = extract_with_bs4(url, client)
                results.append(result)
            except Exception as e:
                results.append({
                    "url": url,
                    "title": "",
                    "content": "",
                    "word_count": 0,
                    "error": str(e),
                })

    return {"success": True, "results": results, "error": ""}


if __name__ == "__main__":
    try:
        input_data = json.load(sys.stdin)
        urls = input_data.get("urls", [])

        if not urls:
            print(json.dumps({"success": True, "results": [], "error": ""}, ensure_ascii=False))
        else:
            result = extract(urls)
            print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"success": False, "results": [], "error": str(e)}, ensure_ascii=False))
        sys.exit(1)
