"""Query source health status from database."""

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
        rows = db.get_source_health()

        sources = []
        unhealthy = []
        for row in rows:
            total = row["total_calls"] or 0
            failures = row["total_failures"] or 0
            entry = {
                "source": row["source"],
                "last_success": row["last_success"],
                "last_failure": row["last_failure"],
                "consecutive_failures": row["consecutive_failures"] or 0,
                "total_calls": total,
                "total_failures": failures,
                "failure_rate": round(failures / total, 3) if total > 0 else 0.0,
            }
            sources.append(entry)
            if (row["consecutive_failures"] or 0) >= 3:
                unhealthy.append(row["source"])

        print(json.dumps({
            "success": True,
            "sources": sources,
            "unhealthy": unhealthy,
            "total_sources": len(sources),
        }, ensure_ascii=False))
    finally:
        db.close()


if __name__ == "__main__":
    main()
