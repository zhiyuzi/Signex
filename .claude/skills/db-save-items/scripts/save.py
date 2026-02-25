"""Save sensor items to SQLite database."""

import io
import json
import os
import sys
from datetime import datetime

# Ensure UTF-8 stdio on all platforms (Windows defaults to GBK/cp936)
for _stream in ('stdin', 'stdout', 'stderr'):
    _cur = getattr(sys, _stream)
    if hasattr(_cur, 'buffer') and _cur.encoding and _cur.encoding.lower().replace('-', '') != 'utf8':
        setattr(sys, _stream, io.TextIOWrapper(_cur.buffer, encoding='utf-8'))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))

from src.store.database import Database
from src.store.models import SensorItem


def clean_string(s: str) -> str:
    """清理字符串中的无效 Unicode 代理字符（Windows 特有问题）"""
    if not isinstance(s, str):
        return s
    return s.encode('utf-8', errors='surrogatepass').decode('utf-8', errors='ignore')


def summarize_item(d: dict) -> dict:
    """Extract compact fields for LLM analysis (saves tokens)."""
    content = clean_string(d.get("content", "") or "")
    if len(content) > 150:
        content = content[:150] + "..."
    return {
        "source": d.get("source", ""),
        "title": clean_string(d.get("title", "")),
        "content": content,
        "url": d.get("url", ""),
    }


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": f"Invalid JSON input: {e}"}, ensure_ascii=False))
        sys.exit(1)

    items_data = input_data.get("items", [])
    watch_name = input_data.get("watch_name")
    sensor_success = input_data.get("success", True)

    if not items_data:
        print(json.dumps({"success": True, "inserted": 0, "total": 0, "item_ids": []}, ensure_ascii=False))
        return

    items = []
    for d in items_data:
        published_at = None
        if d.get("published_at"):
            try:
                published_at = datetime.fromisoformat(d["published_at"])
            except (ValueError, TypeError):
                pass

        items.append(SensorItem(
            source=clean_string(d.get("source", "")),
            source_id=clean_string(d.get("source_id", "")),
            title=clean_string(d.get("title", "")),
            url=clean_string(d.get("url", "")),
            content=clean_string(d.get("content", "")),
            metadata=d.get("metadata", {}),
            published_at=published_at,
        ))

    db = Database()
    db.init()
    try:
        result = db.save_items(items, watch_name=watch_name)

        # Update source health
        sources_seen = set(item.source for item in items)
        for src in sources_seen:
            db.update_source_health(src, sensor_success)

        # Build compact summary for LLM analysis
        summary = [summarize_item(d) for d in items_data]

        print(json.dumps({
            "success": True,
            "inserted": result["inserted"],
            "total": len(items),
            "item_ids": result["item_ids"],
            "summary": summary,
        }, ensure_ascii=False))
    finally:
        db.close()


if __name__ == "__main__":
    main()
