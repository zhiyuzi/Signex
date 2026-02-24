"""Query items from SQLite database."""

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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))

from src.store.database import Database


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", help="Filter by source")
    parser.add_argument("--watch", help="Filter by watch name")
    parser.add_argument("--since", help="Filter by start time (ISO 8601)")
    parser.add_argument("--until", help="Filter by end time (ISO 8601)")
    args = parser.parse_args()

    db = Database()
    db.init()

    try:
        rows = db.get_items(source=args.source, since=args.since, until=args.until)

        # Filter by watch_name if specified
        if args.watch:
            rows = [r for r in rows if r.get("watch_name") == args.watch]

        items = []
        for row in rows:
            item = dict(row)
            if isinstance(item.get("metadata"), str):
                try:
                    item["metadata"] = json.loads(item["metadata"])
                except (json.JSONDecodeError, TypeError):
                    pass
            items.append(item)

        print(json.dumps({"success": True, "items": items, "count": len(items)}, default=str, ensure_ascii=False))
    finally:
        db.close()


if __name__ == "__main__":
    main()
