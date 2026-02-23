"""Save sensor items to SQLite database."""

import io
import json
import os
import re
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
    # 移除 lone surrogates（单独的代理字符无法编码为 UTF-8）
    return s.encode('utf-8', errors='surrogatepass').decode('utf-8', errors='ignore')


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": f"Invalid JSON input: {e}"}, ensure_ascii=False))
        sys.exit(1)

    items_data = input_data.get("items", [])
    sensor_success = input_data.get("success", True)

    if not items_data:
        print(json.dumps({"success": True, "inserted": 0, "total": 0}, ensure_ascii=False))
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
            published_at=published_at
        ))

    db = Database()
    db.init()
    try:
        inserted = db.save_items(items)

        # Update source health
        sources_seen = set(item.source for item in items)
        for src in sources_seen:
            db.update_source_health(src, sensor_success)

        print(json.dumps({"success": True, "inserted": inserted, "total": len(items)}, ensure_ascii=False))
    finally:
        db.close()


if __name__ == "__main__":
    main()
