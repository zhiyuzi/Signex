"""Search academic papers via OpenAlex API."""

import io
import json
import os
import sys
import time

# Ensure UTF-8 stdio on all platforms (Windows defaults to GBK/cp936)
for _stream in ('stdin', 'stdout', 'stderr'):
    _cur = getattr(sys, _stream)
    if hasattr(_cur, 'buffer') and _cur.encoding and _cur.encoding.lower().replace('-', '') != 'utf8':
        setattr(sys, _stream, io.TextIOWrapper(_cur.buffer, encoding='utf-8'))

import httpx
from dotenv import load_dotenv

load_dotenv()

OPENALEX_API = "https://api.openalex.org/works"


def _reconstruct_abstract(inverted_index: dict | None) -> str:
    """Reconstruct abstract text from OpenAlex inverted index format."""
    if not inverted_index:
        return ""
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort()
    return " ".join(w for _, w in word_positions)


def _extract_work_id(openalex_id: str) -> str:
    """Extract short ID from full OpenAlex URL. e.g. https://openalex.org/W123 -> W123"""
    if "/" in openalex_id:
        return openalex_id.rsplit("/", 1)[-1]
    return openalex_id


def search(
    queries: list[str],
    per_page: int = 20,
    publication_year: str | None = None,
    work_type: str | None = None,
    open_access_only: bool = False,
) -> dict:
    api_key = os.getenv("OPENALEX_API_KEY")
    if not api_key:
        return {"success": False, "items": [], "count": 0, "error": "OPENALEX_API_KEY not set"}

    unique: dict[str, tuple[dict, str]] = {}  # work_id -> (work, query)

    with httpx.Client(timeout=15.0) as client:
        for i, query in enumerate(queries):
            if i > 0:
                time.sleep(1)
            try:
                params: dict = {
                    "search": query,
                    "per_page": min(per_page, 200),
                    "sort": "cited_by_count:desc",
                    "api_key": api_key,
                }
                filters = []
                if publication_year:
                    filters.append(f"publication_year:{publication_year}")
                if work_type:
                    filters.append(f"type:{work_type}")
                if open_access_only:
                    filters.append("open_access.is_oa:true")
                if filters:
                    params["filter"] = ",".join(filters)

                resp = client.get(OPENALEX_API, params=params)
                resp.raise_for_status()
                data = resp.json()

                for work in data.get("results", []):
                    try:
                        work_id = _extract_work_id(work.get("id", ""))
                        if not work_id:
                            continue
                        citations = work.get("cited_by_count", 0) or 0
                        if work_id in unique:
                            existing_citations = unique[work_id][0].get("cited_by_count", 0) or 0
                            if citations <= existing_citations:
                                continue
                        unique[work_id] = (work, query)
                    except Exception:
                        continue

            except Exception:
                continue

    items = []
    for work_id, (work, query) in unique.items():
        try:
            abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))
            authorships = work.get("authorships") or []
            authors = [a.get("author", {}).get("display_name", "") for a in authorships[:20]]
            authors = [a for a in authors if a]

            primary_topic = work.get("primary_topic") or {}
            topics = [t.get("display_name", "") for t in (work.get("topics") or [])[:5]]

            oa = work.get("open_access") or {}
            doi = work.get("doi") or ""
            ids = work.get("ids") or {}

            items.append({
                "source": "openalex",
                "source_id": work_id,
                "title": work.get("title") or work.get("display_name") or "",
                "url": doi if doi else f"https://openalex.org/{work_id}",
                "content": abstract,
                "metadata": {
                    "authors": authors,
                    "publication_year": work.get("publication_year"),
                    "type": work.get("type", ""),
                    "cited_by_count": work.get("cited_by_count", 0) or 0,
                    "fwci": work.get("fwci"),
                    "primary_topic": primary_topic.get("display_name", ""),
                    "topics": topics,
                    "is_open_access": oa.get("is_oa", False),
                    "oa_url": oa.get("oa_url", ""),
                    "doi": doi,
                    "external_ids": {k: v for k, v in ids.items() if k != "openalex"},
                    "query": query,
                },
                "published_at": work.get("publication_date"),
            })
        except Exception:
            continue

    return {"success": True, "items": items, "count": len(items), "error": ""}


if __name__ == "__main__":
    try:
        input_data = json.load(sys.stdin)
        queries = input_data.get("queries", [])
        per_page = input_data.get("per_page", 20)
        publication_year = input_data.get("publication_year")
        work_type = input_data.get("type")
        open_access_only = input_data.get("open_access_only", False)

        if not queries:
            print(json.dumps({"success": True, "items": [], "count": 0, "error": ""}, ensure_ascii=False))
        else:
            result = search(queries, per_page, publication_year, work_type, open_access_only)
            print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"success": False, "items": [], "count": 0, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)
