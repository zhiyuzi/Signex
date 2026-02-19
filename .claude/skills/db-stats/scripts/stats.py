"""Output run history statistics from SQLite database."""

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
    db = Database()
    db.init()
    try:
        stats = db.get_run_stats()
        print(json.dumps({"success": True, **stats}, default=str, ensure_ascii=False))
    finally:
        db.close()


if __name__ == "__main__":
    main()
