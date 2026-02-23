from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from src.runtime.init_workspace import ensure_initialized


class InitWorkspaceTests(unittest.TestCase):
    def test_init_creates_expected_directories_files_and_db(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".env.example").write_text("DUMMY=1\n", encoding="utf-8")

            summary = ensure_initialized(root)

            for rel in ["watches", "vault", "profile", "reports", "alerts", "data"]:
                self.assertTrue((root / rel).exists(), rel)

            self.assertTrue((root / "watches/index.md").exists())
            self.assertTrue((root / "vault/index.md").exists())
            self.assertTrue((root / "profile/identity.md").exists())
            self.assertTrue((root / "data/signex.db").exists())
            self.assertTrue(summary.db_initialized)
            self.assertTrue(summary.env_missing)

            second = ensure_initialized(root)
            self.assertEqual(second.created_dirs, [])
            self.assertEqual(second.created_files, [])


if __name__ == "__main__":
    unittest.main()
