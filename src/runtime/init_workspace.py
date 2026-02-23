"""Workspace bootstrap flow shared by Claude and Codex runtimes."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

from src.runtime.common import (
    IDENTITY_TEMPLATE,
    VAULT_INDEX_TEMPLATE,
    WATCH_INDEX_TEMPLATE,
)
from src.store.database import Database


@dataclass
class InitSummary:
    """Result of workspace initialization."""

    created_dirs: list[str] = field(default_factory=list)
    existing_dirs: list[str] = field(default_factory=list)
    created_files: list[str] = field(default_factory=list)
    existing_files: list[str] = field(default_factory=list)
    db_initialized: bool = False
    env_missing: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def _ensure_dir(path: Path, summary: InitSummary) -> None:
    if path.exists():
        summary.existing_dirs.append(str(path))
        return
    path.mkdir(parents=True, exist_ok=True)
    summary.created_dirs.append(str(path))


def _ensure_file(path: Path, content: str, summary: InitSummary) -> None:
    if path.exists():
        summary.existing_files.append(str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    summary.created_files.append(str(path))


def ensure_initialized(root_dir: Path) -> InitSummary:
    """Idempotently create Signex workspace files and DB."""
    root = root_dir.resolve()
    summary = InitSummary()

    for rel in ["watches", "vault", "profile", "reports", "alerts", "data"]:
        _ensure_dir(root / rel, summary)

    _ensure_file(root / "watches/index.md", WATCH_INDEX_TEMPLATE, summary)
    _ensure_file(root / "vault/index.md", VAULT_INDEX_TEMPLATE, summary)
    _ensure_file(root / "profile/identity.md", IDENTITY_TEMPLATE, summary)

    db_path = root / "data/signex.db"
    db = Database(str(db_path))
    db.init()
    db.close()
    summary.db_initialized = True

    summary.env_missing = not (root / ".env").exists() and (root / ".env.example").exists()

    return summary
