"""SQLite database wrapper for Signex."""

import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.store.models import SensorItem


class Database:
    """SQLite database for storing sensor items and analysis records."""

    def __init__(self, db_path: str = "data/signex.db"):
        self.db_path = db_path
        self.connection = None

    def init(self):
        """Initialize database schema."""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row

        cursor = self.connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                source TEXT NOT NULL,
                source_id TEXT,
                title TEXT,
                url TEXT,
                content TEXT,
                metadata JSON,
                fetched_at TIMESTAMP NOT NULL,
                published_at TIMESTAMP,
                UNIQUE(source, source_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY,
                watch_name TEXT NOT NULL,
                run_at TIMESTAMP NOT NULL,
                item_count INTEGER NOT NULL DEFAULT 0,
                lens TEXT,
                report_path TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_items (
                analysis_id INTEGER REFERENCES analyses(id),
                item_id INTEGER REFERENCES items(id),
                PRIMARY KEY (analysis_id, item_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS source_health (
                source TEXT PRIMARY KEY,
                last_success TEXT,
                last_failure TEXT,
                consecutive_failures INTEGER DEFAULT 0,
                total_calls INTEGER DEFAULT 0,
                total_failures INTEGER DEFAULT 0
            )
        """)

        self.connection.commit()

    def save_items(self, items: list[SensorItem]) -> int:
        """Save items to database with deduplication.

        Returns count of newly inserted items.
        """
        if not self.connection:
            raise RuntimeError("Database not initialized. Call init() first.")

        cursor = self.connection.cursor()
        inserted_count = 0

        for item in items:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO items
                    (source, source_id, title, url, content, metadata, fetched_at, published_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.source,
                    item.source_id,
                    item.title,
                    item.url,
                    item.content,
                    json.dumps(item.metadata, ensure_ascii=False) if item.metadata else None,
                    datetime.now(timezone.utc).isoformat(),
                    item.published_at.isoformat() if item.published_at else None
                ))

                if cursor.rowcount > 0:
                    inserted_count += 1
            except sqlite3.Error:
                continue

        self.connection.commit()
        return inserted_count

    def get_items(
        self,
        source: str | None = None,
        since: str | None = None,
        until: str | None = None
    ) -> list[dict[str, Any]]:
        """Query items with optional filters.

        Args:
            source: Filter by source name
            since: Filter items fetched after this ISO timestamp
            until: Filter items fetched before this ISO timestamp

        Returns:
            List of item dicts with id included.
        """
        if not self.connection:
            raise RuntimeError("Database not initialized. Call init() first.")

        query = "SELECT * FROM items WHERE 1=1"
        params: list[Any] = []

        if source:
            query += " AND source = ?"
            params.append(source)

        if since:
            query += " AND fetched_at >= ?"
            params.append(since)

        if until:
            query += " AND fetched_at <= ?"
            params.append(until)

        query += " ORDER BY fetched_at DESC"

        cursor = self.connection.cursor()
        cursor.execute(query, params)

        return [dict(row) for row in cursor.fetchall()]

    def get_unanalyzed_items(
        self,
        watch_name: str,
        source: str | None = None
    ) -> list[dict[str, Any]]:
        """Get items not yet analyzed by this watch.

        Returns list of item dicts with id included.
        """
        if not self.connection:
            raise RuntimeError("Database not initialized. Call init() first.")

        query = """
            SELECT i.* FROM items i
            WHERE i.id NOT IN (
                SELECT ai.item_id FROM analysis_items ai
                JOIN analyses a ON ai.analysis_id = a.id
                WHERE a.watch_name = ?
            )
        """
        params: list[Any] = [watch_name]

        if source:
            query += " AND i.source = ?"
            params.append(source)

        query += " ORDER BY i.fetched_at DESC"

        cursor = self.connection.cursor()
        cursor.execute(query, params)

        return [dict(row) for row in cursor.fetchall()]

    def save_analysis(
        self,
        watch_name: str,
        item_ids: list[int],
        report_path: str,
        item_count: int,
        lens: str
    ) -> int:
        """Save analysis record and link to analyzed items.

        Returns the analysis_id.
        """
        if not self.connection:
            raise RuntimeError("Database not initialized. Call init() first.")

        cursor = self.connection.cursor()

        cursor.execute("""
            INSERT INTO analyses (watch_name, run_at, item_count, lens, report_path)
            VALUES (?, ?, ?, ?, ?)
        """, (
            watch_name,
            datetime.now(timezone.utc).isoformat(),
            item_count,
            lens,
            report_path
        ))

        analysis_id = cursor.lastrowid

        for item_id in item_ids:
            cursor.execute("""
                INSERT OR IGNORE INTO analysis_items (analysis_id, item_id)
                VALUES (?, ?)
            """, (analysis_id, item_id))

        self.connection.commit()
        return analysis_id

    def get_run_stats(self) -> dict[str, Any]:
        """Get run history statistics.

        Returns:
            {
                "by_watch": {"watch-name": {"runs": N, "total_items": N, "last_run": "...", "lenses": [...]}},
                "by_date": {"2026-02-17": {"runs": N, "total_items": N}},
                "totals": {"runs": N, "total_items": N}
            }
        """
        if not self.connection:
            raise RuntimeError("Database not initialized. Call init() first.")

        cursor = self.connection.cursor()
        cursor.execute("SELECT watch_name, run_at, item_count, lens FROM analyses ORDER BY run_at DESC")

        by_watch: dict[str, Any] = {}
        by_date: dict[str, Any] = {}
        total_runs = 0
        total_items = 0

        for row in cursor.fetchall():
            watch_name = row["watch_name"]
            run_at = row["run_at"]
            item_count = row["item_count"] or 0
            lens = row["lens"] or ""

            # By watch
            if watch_name not in by_watch:
                by_watch[watch_name] = {
                    "runs": 0,
                    "total_items": 0,
                    "last_run": run_at,
                    "lenses": []
                }
            by_watch[watch_name]["runs"] += 1
            by_watch[watch_name]["total_items"] += item_count
            if lens and lens not in by_watch[watch_name]["lenses"]:
                by_watch[watch_name]["lenses"].append(lens)

            # By date
            date_str = run_at.split("T")[0] if "T" in run_at else run_at.split(" ")[0]
            if date_str not in by_date:
                by_date[date_str] = {"runs": 0, "total_items": 0}
            by_date[date_str]["runs"] += 1
            by_date[date_str]["total_items"] += item_count

            total_runs += 1
            total_items += item_count

        return {
            "by_watch": by_watch,
            "by_date": by_date,
            "totals": {"runs": total_runs, "total_items": total_items}
        }

    def update_source_health(self, source: str, success: bool) -> None:
        """Update health tracking for a sensor source."""
        if not self.connection:
            raise RuntimeError("Database not initialized. Call init() first.")

        cursor = self.connection.cursor()
        now = datetime.now(timezone.utc).isoformat()

        cursor.execute("""
            INSERT INTO source_health (source, last_success, last_failure, consecutive_failures, total_calls, total_failures)
            VALUES (?, ?, ?, ?, 1, ?)
            ON CONFLICT(source) DO UPDATE SET
                last_success = CASE WHEN ? THEN ? ELSE last_success END,
                last_failure = CASE WHEN ? THEN ? ELSE last_failure END,
                consecutive_failures = CASE WHEN ? THEN 0 ELSE consecutive_failures + 1 END,
                total_calls = total_calls + 1,
                total_failures = CASE WHEN ? THEN total_failures ELSE total_failures + 1 END
        """, (
            source,
            now if success else None,
            None if success else now,
            0 if success else 1,
            0 if success else 1,
            success, now,
            not success, now,
            success,
            success,
        ))

        self.connection.commit()

    def get_source_health(self) -> list[dict[str, Any]]:
        """Get health status for all tracked sources."""
        if not self.connection:
            raise RuntimeError("Database not initialized. Call init() first.")

        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM source_health ORDER BY source")
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
