"""Summarize sensor items for LLM analysis.

Reads full sensor JSON from stdin, outputs a compact summary:
- Only title, content snippet (first 150 chars), url, source
- Strips metadata, published_at, and other fields
- Designed to reduce token consumption by ~90%

Usage:
    echo '{"items": [...]}' | uv run python .claude/skills/db-save-items/scripts/summarize.py
    # or with item limit:
    echo '{"items": [...]}' | uv run python .claude/skills/db-save-items/scripts/summarize.py --limit 80
"""

import argparse
import io
import json
import sys

# Ensure UTF-8 stdio on all platforms
for _stream in ('stdin', 'stdout', 'stderr'):
    _cur = getattr(sys, _stream)
    if hasattr(_cur, 'buffer') and _cur.encoding and _cur.encoding.lower().replace('-', '') != 'utf8':
        setattr(sys, _stream, io.TextIOWrapper(_cur.buffer, encoding='utf-8'))


def summarize_item(item: dict) -> dict:
    """Extract only the fields needed for LLM analysis."""
    content = item.get("content", "") or ""
    # Truncate content to first 150 chars
    if len(content) > 150:
        content = content[:150] + "..."

    return {
        "source": item.get("source", ""),
        "title": item.get("title", ""),
        "content": content,
        "url": item.get("url", ""),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Max items to output (0 = all)")
    args = parser.parse_args()

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)

    items = input_data.get("items", [])

    if args.limit > 0:
        items = items[:args.limit]

    summarized = [summarize_item(item) for item in items]

    print(json.dumps({
        "success": True,
        "items": summarized,
        "count": len(summarized),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
