"""Lightweight natural-language intent router for Codex runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re


WATCH_NAME_PATTERNS = [
    re.compile(r"(?:run|execute)\s+(?:watch\s+)?([a-zA-Z0-9][a-zA-Z0-9_-]{1,63})", flags=re.IGNORECASE),
    re.compile(r"(?:跑一下|运行|执行)\s*([a-zA-Z0-9][a-zA-Z0-9_-]{1,63})"),
    re.compile(r"([a-zA-Z0-9][a-zA-Z0-9_-]{1,63})\s*(?:watch)?\s*(?:跑一下|运行|执行)", flags=re.IGNORECASE),
]

LENS_PATTERNS = {
    "flash_brief": re.compile(r"flash|brief|速览|快速", flags=re.IGNORECASE),
    "dual_take": re.compile(r"dual|pro\s*/\s*con|正反|利弊", flags=re.IGNORECASE),
    "timeline_trace": re.compile(r"timeline|时间线|脉络", flags=re.IGNORECASE),
    "deep_insight": re.compile(r"deep|insight|深度", flags=re.IGNORECASE),
}


@dataclass
class RouteResult:
    intent: str
    watch_name: str = ""
    lens: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


def _extract_watch_name(text: str) -> str:
    for pattern in WATCH_NAME_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1)

    quoted = re.search(r"['\"]([a-zA-Z0-9][a-zA-Z0-9_-]{1,63})['\"]", text)
    if quoted:
        return quoted.group(1)

    return ""


def _extract_lens(text: str) -> str:
    for lens, pattern in LENS_PATTERNS.items():
        if pattern.search(text):
            return lens
    return ""


def route_message(user_text: str) -> RouteResult:
    """Route user message into runtime intents."""
    text = user_text.strip()
    lower = text.lower()

    if lower in {"hi", "hello", "hey", "你好", "嗨", "早上好", "晚上好"}:
        return RouteResult(intent="greeting", confidence=0.99)

    watch_name = _extract_watch_name(text)
    lens = _extract_lens(text)

    run_hit = bool(re.search(r"\b(run|execute|start)\b|跑一下|运行|执行", text, flags=re.IGNORECASE))
    if run_hit and watch_name:
        return RouteResult(intent="run_watch", watch_name=watch_name, lens=lens, confidence=0.94)

    if run_hit:
        return RouteResult(intent="run_watch", lens=lens, confidence=0.75)

    status_hit = bool(re.search(r"\b(status|stats|health|overview)\b|状态|统计|健康|态势", text, flags=re.IGNORECASE))
    if status_hit:
        return RouteResult(intent="query_status", confidence=0.85)

    update_hit = bool(re.search(r"更新|调整|加个关注|不要再关注|exclude|focus", text, flags=re.IGNORECASE))
    if update_hit:
        return RouteResult(intent="update_watch", watch_name=watch_name, confidence=0.75)

    return RouteResult(intent="unknown", confidence=0.25)
