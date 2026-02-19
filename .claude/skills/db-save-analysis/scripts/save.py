"""Save analysis record to SQLite database."""

import io
import json
import os
import sys

# Ensure UTF-8 stdio on all platforms (Windows defaults to GBK/cp936)
for _stream in ('stdin', 'stdout', 'stderr'):
    _cur = getattr(sys, _stream)
    if hasattr(_cur, 'buffer') and _cur.encoding and _cur.encoding.lower().replace('-', '') != 'utf8':
        setattr(sys, _stream, io.TextIOWrapper(_cur.buffer, encoding='utf-8'))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))

from src.store.database import Database


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": f"Invalid JSON input: {e}"}, ensure_ascii=False))
        sys.exit(1)

    watch_name = input_data.get("watch_name", "")
    item_ids = input_data.get("item_ids", [])
    report_path = input_data.get("report_path", "")
    item_count = input_data.get("item_count", 0)
    lens = input_data.get("lens", "")

    if not watch_name:
        print(json.dumps({"success": False, "error": "watch_name is required"}, ensure_ascii=False))
        sys.exit(1)

    db = Database()
    db.init()
    try:
        analysis_id = db.save_analysis(
            watch_name=watch_name,
            item_ids=item_ids,
            report_path=report_path,
            item_count=item_count,
            lens=lens
        )
        print(json.dumps({"success": True, "analysis_id": analysis_id}, ensure_ascii=False))
    finally:
        db.close()


if __name__ == "__main__":
    main()
