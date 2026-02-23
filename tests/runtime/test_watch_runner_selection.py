from __future__ import annotations

from datetime import datetime, timezone
import unittest

from src.runtime.watch_runner import generate_search_queries, select_sensors


class WatchRunnerSelectionTests(unittest.TestCase):
    def test_sensor_selection_for_academic_watch(self) -> None:
        intent = """
# ai-research

## Focus
Track papers, preprints, and academic trends in LLM agents.
"""
        sensors = select_sensors(intent, "")
        self.assertIn("fetch-arxiv", sensors)
        self.assertIn("fetch-openalex", sensors)
        self.assertIn("fetch-hacker-news", sensors)

    def test_search_queries_include_year_month(self) -> None:
        now = datetime(2026, 2, 23, 10, 0, tzinfo=timezone.utc)
        queries = generate_search_queries(
            watch_name="ai-coding-tools",
            intent_text="- Cursor updates\n- Agent IDE workflows",
            memory_text="",
            now=now,
        )
        self.assertTrue(queries)
        self.assertTrue(all("2026-02" in q for q in queries[:2]))


if __name__ == "__main__":
    unittest.main()
