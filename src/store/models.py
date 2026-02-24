"""Data models for Signex."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SensorItem:
    """A single data item fetched by a sensor."""

    source: str
    source_id: str
    title: str
    url: str = ""
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    published_at: datetime | None = None
    watch_name: str | None = None
