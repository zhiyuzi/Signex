from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from src.runtime.watch_runner import update_watch_state


class StateUpdateTests(unittest.TestCase):
    def test_state_last_run_is_timezone_iso(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            state_path.write_text(
                json.dumps({"check_interval": "1d", "status": "active", "last_run": None}, ensure_ascii=False),
                encoding="utf-8",
            )

            now = datetime(2026, 2, 23, 9, 30, tzinfo=timezone.utc)
            state = update_watch_state(state_path, now=now)

            self.assertEqual(state["status"], "active")
            self.assertEqual(state["check_interval"], "1d")
            self.assertEqual(state["last_run"], "2026-02-23T09:30:00+00:00")

            loaded = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["last_run"], "2026-02-23T09:30:00+00:00")


if __name__ == "__main__":
    unittest.main()
