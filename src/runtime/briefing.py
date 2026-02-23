"""Status briefing helpers for the `signex hi` command."""

from __future__ import annotations

from datetime import datetime, timedelta
import json
from pathlib import Path
import re
from typing import Any

from src.runtime.common import language_from_context, read_text


def _parse_watch_names(index_text: str) -> list[str]:
    names: list[str] = []
    for line in index_text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        if "Watch" in line and "Description" in line:
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 3:
            continue
        watch_name = parts[1]
        if watch_name and watch_name != "-------" and watch_name not in names:
            names.append(watch_name)
    return names


def _interval_to_timedelta(raw: str | None) -> timedelta:
    if not raw:
        return timedelta(days=1)
    text = raw.strip().lower()
    match = re.match(r"^(\d+)\s*([hdwm])$", text)
    if not match:
        return timedelta(days=1)
    amount = int(match.group(1))
    unit = match.group(2)
    if unit == "h":
        return timedelta(hours=amount)
    if unit == "d":
        return timedelta(days=amount)
    if unit == "w":
        return timedelta(weeks=amount)
    return timedelta(days=amount * 30)


def _watch_state(root_dir: Path, watch_name: str) -> dict[str, Any]:
    state_path = root_dir / "watches" / watch_name / "state.json"
    if not state_path.exists():
        return {"watch": watch_name, "status": "unknown", "check_interval": "1d", "last_run": None, "due": True}

    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        state = {}

    status = state.get("status", "active")
    check_interval = state.get("check_interval", "1d")
    last_run = state.get("last_run")

    due = status == "active"
    if last_run and status == "active":
        try:
            last = datetime.fromisoformat(last_run.replace("Z", "+00:00"))
            due = datetime.now().astimezone() >= (last + _interval_to_timedelta(check_interval))
        except ValueError:
            due = True

    return {
        "watch": watch_name,
        "status": status,
        "check_interval": check_interval,
        "last_run": last_run,
        "due": due,
    }


def _today_outputs(root_dir: Path, date_str: str) -> tuple[int, int]:
    report_dir = root_dir / "reports" / date_str
    alert_dir = root_dir / "alerts" / date_str
    report_count = len(list(report_dir.rglob("insights.md"))) if report_dir.exists() else 0
    alert_count = len(list(alert_dir.glob("*.md"))) if alert_dir.exists() else 0
    return report_count, alert_count


def build_briefing(root_dir: Path, fallback_user_text: str = "") -> tuple[str, dict[str, Any]]:
    """Build a short situational briefing from local watch state."""
    root = root_dir.resolve()
    identity_text = read_text(root / "profile/identity.md")
    watch_index_text = read_text(root / "watches/index.md")
    language = language_from_context(identity_text, fallback_user_text)

    watch_names = _parse_watch_names(watch_index_text)
    if not watch_names:
        watches_dir = root / "watches"
        if watches_dir.exists():
            for watch_dir in sorted(watches_dir.iterdir()):
                if watch_dir.is_dir():
                    watch_names.append(watch_dir.name)

    watch_states = [_watch_state(root, name) for name in watch_names]
    active = [w for w in watch_states if w["status"] == "active"]
    due = [w for w in active if w["due"]]
    paused = [w for w in watch_states if w["status"] == "paused"]

    today = datetime.now().astimezone().strftime("%Y-%m-%d")
    report_count, alert_count = _today_outputs(root, today)

    if language == "zh":
        lines = [
            f"你当前有 {len(active)} 个活跃 Watch，{len(paused)} 个暂停。",
            f"今天（{today}）已产出 {report_count} 份报告、{alert_count} 条 alert。",
        ]
        if due:
            due_names = ", ".join(w["watch"] for w in due[:4])
            lines.append(f"建议优先运行这些已到期 Watch：{due_names}。")
        else:
            lines.append("当前没有到期 Watch，可以按需手动运行。")
    else:
        lines = [
            f"You currently have {len(active)} active watches and {len(paused)} paused.",
            f"Today ({today}) produced {report_count} report(s) and {alert_count} alert(s).",
        ]
        if due:
            due_names = ", ".join(w["watch"] for w in due[:4])
            lines.append(f"Recommended next run: {due_names}.")
        else:
            lines.append("No watch is due right now; run one on demand if needed.")

    payload = {
        "language": language,
        "date": today,
        "active_count": len(active),
        "paused_count": len(paused),
        "due_watches": [w["watch"] for w in due],
        "report_count_today": report_count,
        "alert_count_today": alert_count,
        "watch_states": watch_states,
    }
    return "\n".join(lines), payload
