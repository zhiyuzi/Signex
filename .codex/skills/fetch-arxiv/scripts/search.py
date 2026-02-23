"""Search arXiv for academic preprints via the public API."""

import io
import json
import re
import sys
import time

# Ensure UTF-8 stdio on all platforms (Windows defaults to GBK/cp936)
for _stream in ('stdin', 'stdout', 'stderr'):
    _cur = getattr(sys, _stream)
    if hasattr(_cur, 'buffer') and _cur.encoding and _cur.encoding.lower().replace('-', '') != 'utf8':
        setattr(sys, _stream, io.TextIOWrapper(_cur.buffer, encoding='utf-8'))

import feedparser
import httpx

ARXIV_API = "http://export.arxiv.org/api/query"
ARXIV_ID_RE = re.compile(r"(\d{4}\.\d{4,5})")


def _build_query(keyword: str, categories: list[str] | None) -> str:
    """Build arXiv search_query string."""
    q = f"all:{keyword}"
    if categories:
        cat_expr = "+OR+".join(f"cat:{c}" for c in categories)
        q = f"{q}+AND+({cat_expr})"
    return q


def _extract_arxiv_id(entry_id: str) -> str:
    """Extract bare arXiv ID (no version) from entry URL."""
    m = ARXIV_ID_RE.search(entry_id)
    return m.group(1) if m else entry_id


def _parse_entry(entry, query: str) -> dict | None:
    """Parse a single Atom entry into standard item dict."""
    entry_id = entry.get("id", "")
    arxiv_id = _extract_arxiv_id(entry_id)
    if not arxiv_id:
        return None

    title = entry.get("title", "").replace("\n", " ").strip()
    abstract = entry.get("summary", "").strip()

    authors = []
    for a in entry.get("authors", []):
        name = a.get("name", "")
        if name:
            authors.append(name)

    categories = []
    primary_category = ""
    for tag in entry.get("tags", []):
        term = tag.get("term", "")
        if term:
            categories.append(term)
    if categories:
        primary_category = categories[0]

    # Find PDF link
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
    for link in entry.get("links", []):
        if link.get("type") == "application/pdf":
            pdf_url = link.get("href", pdf_url)
            break

    comment = entry.get("arxiv_comment", None)
    journal_ref = entry.get("arxiv_journal_ref", None)
    doi = entry.get("arxiv_doi", None)
    published = entry.get("published", None)

    return {
        "source": "arxiv",
        "source_id": arxiv_id,
        "title": title,
        "url": f"https://arxiv.org/abs/{arxiv_id}",
        "content": abstract,
        "metadata": {
            "authors": authors,
            "categories": categories,
            "primary_category": primary_category,
            "pdf_url": pdf_url,
            "comment": comment,
            "journal_ref": journal_ref,
            "doi": doi,
            "query": query,
        },
        "published_at": published,
    }


def search(
    queries: list[str],
    categories: list[str] | None = None,
    max_results: int = 20,
    sort_by: str = "submittedDate",
    sort_order: str = "descending",
) -> dict:
    max_results = min(max_results, 100)
    seen: dict[str, dict] = {}  # arxiv_id -> item (dedup)

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for i, query in enumerate(queries):
            if i > 0:
                time.sleep(3)  # polite rate limiting

            try:
                search_query = _build_query(query, categories)
                params = {
                    "search_query": search_query,
                    "start": 0,
                    "max_results": max_results,
                    "sortBy": sort_by,
                    "sortOrder": sort_order,
                }
                resp = client.get(
                    ARXIV_API,
                    params=params,
                    headers={"User-Agent": "Signex/1.0 arXiv Sensor"},
                )
                resp.raise_for_status()

                feed = feedparser.parse(resp.text)
                for entry in feed.entries:
                    try:
                        item = _parse_entry(entry, query)
                        if item and item["source_id"] not in seen:
                            seen[item["source_id"]] = item
                    except Exception:
                        continue

            except Exception:
                continue

    items = list(seen.values())
    return {"success": True, "items": items, "count": len(items), "error": ""}


if __name__ == "__main__":
    try:
        input_data = json.load(sys.stdin)
        queries = input_data.get("queries", [])
        categories = input_data.get("categories")
        max_results = input_data.get("max_results", 20)
        sort_by = input_data.get("sort_by", "submittedDate")
        sort_order = input_data.get("sort_order", "descending")

        if not queries:
            print(json.dumps({"success": True, "items": [], "count": 0, "error": ""}, ensure_ascii=False))
        else:
            result = search(queries, categories, max_results, sort_by, sort_order)
            print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"success": False, "items": [], "count": 0, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)
