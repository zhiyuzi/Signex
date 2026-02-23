"""Shared helpers for the Codex-compatible Signex runtime."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

ROOT_DIR = Path(__file__).resolve().parents[2]

WATCH_INDEX_TEMPLATE = """# Watches

| Watch | Description | Status |
|-------|-------------|--------|
"""

VAULT_INDEX_TEMPLATE = """# Vault

| Title | Summary | File | Tags |
|-------|---------|------|------|
"""

IDENTITY_TEMPLATE = """# User Identity

(Edit this file to describe yourself. All Watches reference this profile.)

## Background
- Role: (e.g., independent developer, product manager, researcher)
- Domain: (e.g., AI/ML, web development, fintech)

## Preferences
- Report language: (e.g., Chinese, English)
- Focus: actionable insights over raw data
"""


def now_iso_with_tz(current: datetime | None = None) -> str:
    """Return ISO 8601 timestamp with explicit timezone offset."""
    dt = current or datetime.now().astimezone()
    return dt.isoformat(timespec="seconds")


def read_text(path: Path, default: str = "") -> str:
    """Read UTF-8 text, returning default when the file does not exist."""
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8")


def has_chinese(text: str) -> bool:
    """Return True when input has at least one CJK character."""
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def parse_report_language(identity_text: str) -> str | None:
    """Extract report language preference from identity markdown."""
    match = re.search(r"-\s*Report language\s*:\s*(.+)", identity_text, flags=re.IGNORECASE)
    if not match:
        return None
    value = match.group(1).strip().lower()
    if not value or value.startswith("("):
        return None
    if "chinese" in value or "中文" in value:
        return "zh"
    if "english" in value or "英文" in value:
        return "en"
    return None


def language_from_context(identity_text: str, fallback_user_text: str = "") -> str:
    """Resolve output language using identity > input-language > default-en fallback."""
    preferred = parse_report_language(identity_text)
    if preferred:
        return preferred
    if fallback_user_text and has_chinese(fallback_user_text):
        return "zh"
    return "en"
