from __future__ import annotations

import unittest

from src.runtime.router import route_message


class RouterTests(unittest.TestCase):
    def test_greeting_route(self) -> None:
        result = route_message("Hi")
        self.assertEqual(result.intent, "greeting")

    def test_run_watch_route_zh(self) -> None:
        result = route_message("跑一下 ai-coding-tools")
        self.assertEqual(result.intent, "run_watch")
        self.assertEqual(result.watch_name, "ai-coding-tools")

    def test_run_watch_route_en(self) -> None:
        result = route_message("run watch ai-coding-tools with dual take")
        self.assertEqual(result.intent, "run_watch")
        self.assertEqual(result.watch_name, "ai-coding-tools")
        self.assertEqual(result.lens, "dual_take")

    def test_status_route(self) -> None:
        result = route_message("看下当前状态")
        self.assertEqual(result.intent, "query_status")


if __name__ == "__main__":
    unittest.main()
