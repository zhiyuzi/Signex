"""Codex-compatible watch orchestration built on existing .claude skill scripts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

from src.runtime.common import has_chinese, now_iso_with_tz, read_text


SUPPORTED_LENSES = {"deep_insight", "flash_brief", "dual_take", "timeline_trace"}

SENSOR_SCRIPT_PATHS = {
    "fetch-hacker-news": ".claude/skills/fetch-hacker-news/scripts/fetch.py",
    "fetch-github-trending": ".claude/skills/fetch-github-trending/scripts/fetch.py",
    "fetch-v2ex": ".claude/skills/fetch-v2ex/scripts/fetch.py",
    "fetch-tavily": ".claude/skills/fetch-tavily/scripts/search.py",
    "fetch-brave-search": ".claude/skills/fetch-brave-search/scripts/search.py",
    "fetch-exa": ".claude/skills/fetch-exa/scripts/search.py",
    "fetch-product-hunt": ".claude/skills/fetch-product-hunt/scripts/fetch.py",
    "fetch-request-hunt": ".claude/skills/fetch-request-hunt/scripts/search.py",
    "fetch-rss": ".claude/skills/fetch-rss/scripts/fetch.py",
    "fetch-reddit": ".claude/skills/fetch-reddit/scripts/fetch.py",
    "fetch-x": ".claude/skills/fetch-x/scripts/search.py",
    "fetch-news-api": ".claude/skills/fetch-news-api/scripts/search.py",
    "fetch-gnews": ".claude/skills/fetch-gnews/scripts/search.py",
    "fetch-arxiv": ".claude/skills/fetch-arxiv/scripts/search.py",
    "fetch-openalex": ".claude/skills/fetch-openalex/scripts/search.py",
}

DB_SAVE_ITEMS_SCRIPT = ".claude/skills/db-save-items/scripts/save.py"
DB_QUERY_SCRIPT = ".claude/skills/db-query-items/scripts/query.py"
DB_SAVE_ANALYSIS_SCRIPT = ".claude/skills/db-save-analysis/scripts/save.py"


@dataclass
class SensorRunResult:
    sensor: str
    success: bool
    items: list[dict[str, Any]]
    error: str = ""
    inserted: int = 0


def _extract_json(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    if not text:
        return {}

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    for line in reversed(text.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue

    return {}


def _run_json_script(
    root_dir: Path,
    script_rel: str,
    payload: dict[str, Any] | None = None,
    args: list[str] | None = None,
    timeout: int = 180,
) -> tuple[dict[str, Any], str]:
    script_path = root_dir / script_rel
    cmd = [sys.executable, str(script_path)] + (args or [])

    stdin_text = None
    if payload is not None:
        stdin_text = json.dumps(payload, ensure_ascii=False)

    proc = subprocess.run(
        cmd,
        cwd=str(root_dir),
        input=stdin_text,
        text=True,
        capture_output=True,
        timeout=timeout,
    )

    data = _extract_json(proc.stdout)
    if not data:
        data = {
            "success": False,
            "items": [],
            "count": 0,
            "error": proc.stderr.strip() or "Script returned non-JSON output",
        }

    if proc.returncode != 0 and "success" not in data:
        data["success"] = False

    stderr = proc.stderr.strip()
    return data, stderr


def _extract_feed_urls(text: str) -> list[str]:
    urls = re.findall(r"https?://[^\s)]+", text)
    return [u.rstrip(".,") for u in urls]


def _safe_words_from_markdown(markdown_text: str) -> list[str]:
    phrases: list[str] = []
    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if line.startswith("-"):
            line = line[1:].strip()
        line = re.sub(r"^\*\*|\*\*$", "", line)
        line = re.sub(r"\([^)]*\)", "", line).strip()
        if not line:
            continue
        if line.lower().startswith(("role:", "domain:", "report language:", "focus:")):
            continue
        phrases.append(line)
    return phrases


def generate_search_queries(
    watch_name: str,
    intent_text: str,
    memory_text: str,
    now: datetime | None = None,
    max_queries: int = 6,
) -> list[str]:
    """Generate date-scoped queries for search-style sensors."""
    clock = now or datetime.now().astimezone()
    month_tag = clock.strftime("%Y-%m")

    candidate_phrases: list[str] = []
    candidate_phrases.extend(_safe_words_from_markdown(intent_text))

    # memory may contain strict preferences worth carrying to searches
    for phrase in _safe_words_from_markdown(memory_text):
        if any(token in phrase.lower() for token in ["focus", "关注", "偏好", "prefer", "track"]):
            candidate_phrases.append(phrase)

    candidate_phrases.append(watch_name.replace("-", " "))

    excludes: set[str] = set()
    for line in _safe_words_from_markdown(memory_text + "\n" + intent_text):
        if any(token in line.lower() for token in ["exclude", "排除", "不要", "ignore"]):
            for token in re.split(r"[,，/;；\s]+", line):
                if len(token) >= 2:
                    excludes.add(token.lower())

    dedup: list[str] = []
    for phrase in candidate_phrases:
        compact = re.sub(r"\s+", " ", phrase).strip(" :-")
        if not compact:
            continue
        lower = compact.lower()
        if any(x in lower for x in excludes):
            continue
        if lower in [q.lower() for q in dedup]:
            continue
        dedup.append(compact)

    queries: list[str] = []
    for phrase in dedup:
        queries.append(f"{phrase} {month_tag}")
        if has_chinese(phrase):
            queries.append(f"{phrase} 最新 {month_tag}")

    if not queries:
        queries = [f"{watch_name.replace('-', ' ')} {month_tag}"]

    return queries[:max_queries]


def select_sensors(intent_text: str, memory_text: str, max_sensors: int = 6) -> list[str]:
    """Choose the minimal relevant sensor set based on watch context."""
    text = f"{intent_text}\n{memory_text}".lower()
    sensors: list[str] = []

    def add(sensor: str) -> None:
        if sensor in SENSOR_SCRIPT_PATHS and sensor not in sensors:
            sensors.append(sensor)

    add("fetch-hacker-news")

    if any(k in text for k in ["github", "开源", "open source", "repo", "仓库"]):
        add("fetch-github-trending")

    if has_chinese(text) or any(k in text for k in ["中文", "国内", "v2ex"]):
        add("fetch-v2ex")

    if any(k in text for k in ["search", "趋势", "latest", "追踪", "watch", "monitor"]):
        add("fetch-tavily")

    if any(k in text for k in ["reddit", "社区", "讨论", "用户反馈", "pain point", "论坛"]):
        add("fetch-reddit")

    if any(k in text for k in ["新闻", "news", "industry", "行业", "媒体"]):
        add("fetch-news-api")
        add("fetch-gnews")

    if any(k in text for k in ["product", "launch", "新品", "发布", "app"]):
        add("fetch-product-hunt")

    if any(k in text for k in ["request", "需求", "痛点", "feature"]):
        add("fetch-request-hunt")

    if any(k in text for k in ["x", "twitter", "社交", "实时"]):
        add("fetch-x")

    if any(k in text for k in ["rss", "博客", "blog", "changelog"]):
        add("fetch-rss")

    if any(k in text for k in ["paper", "论文", "research", "学术", "preprint"]):
        add("fetch-arxiv")
        add("fetch-openalex")

    if len(sensors) < 3:
        add("fetch-github-trending")
        add("fetch-tavily")

    return sensors[:max_sensors]


def infer_lens(memory_text: str, override: str | None = None) -> str:
    if override in SUPPORTED_LENSES:
        return override

    memo = memory_text.lower()
    if any(k in memo for k in ["flash", "速览", "quick brief"]):
        return "flash_brief"
    if any(k in memo for k in ["dual", "正反", "利弊"]):
        return "dual_take"
    if any(k in memo for k in ["timeline", "时间线", "脉络"]):
        return "timeline_trace"
    return "deep_insight"


def _language_code(intent_text: str, identity_text: str) -> str:
    lower = identity_text.lower()
    if "report language" in lower and ("chinese" in lower or "中文" in lower):
        return "zh"
    if has_chinese(intent_text):
        return "zh"
    return "en"


def _academic_queries(queries: list[str]) -> list[str]:
    academic = []
    for q in queries:
        if any(k in q.lower() for k in ["llm", "agent", "model", "code", "paper", "research", "ai"]):
            academic.append(q)
    if not academic:
        academic = ["large language model agent", "code generation LLM"]
    return academic[:3]


def _default_subreddits(intent_text: str) -> list[str]:
    text = intent_text.lower()
    if any(k in text for k in ["startup", "创业", "saas"]):
        return ["startups", "SaaS", "entrepreneur"]
    if any(k in text for k in ["ai", "llm", "machine learning", "人工智能"]):
        return ["MachineLearning", "LocalLLaMA", "artificial"]
    return ["programming", "technology", "opensource"]


def _sensor_payload(
    sensor: str,
    queries: list[str],
    intent_text: str,
    identity_text: str,
    now: datetime,
) -> tuple[dict[str, Any] | None, list[str] | None]:
    lang = _language_code(intent_text, identity_text)

    if sensor in {"fetch-hacker-news", "fetch-github-trending", "fetch-v2ex"}:
        return None, None

    if sensor == "fetch-product-hunt":
        return None, ["--limit", "20", "--featured"]

    if sensor == "fetch-rss":
        feeds = _extract_feed_urls(intent_text)
        return {"feeds": feeds, "max_per_feed": 20}, None

    if sensor == "fetch-reddit":
        return {"subreddits": _default_subreddits(intent_text), "sort": "hot", "limit": 25}, None

    if sensor == "fetch-tavily":
        return {"queries": queries[:4], "days": 7}, None

    if sensor == "fetch-brave-search":
        return {"queries": queries[:2], "count": 10}, None

    if sensor == "fetch-exa":
        return {"queries": queries[:4], "num_results": 10, "days": 7}, None

    if sensor == "fetch-request-hunt":
        return {"queries": queries[:3], "limit": 20}, None

    if sensor == "fetch-news-api":
        return {"queries": queries[:3], "days": 7, "language": lang}, None

    if sensor == "fetch-gnews":
        return {"queries": queries[:3], "max_results": 10, "language": lang}, None

    if sensor == "fetch-x":
        compact_queries = [q[:60] for q in queries[:3]]
        return {"queries": compact_queries, "max_results": 10, "min_likes": 5}, None

    if sensor == "fetch-arxiv":
        return {
            "queries": _academic_queries(queries),
            "categories": ["cs.AI", "cs.CL", "cs.SE"],
            "max_results": 20,
        }, None

    if sensor == "fetch-openalex":
        return {
            "queries": _academic_queries(queries),
            "per_page": 20,
            "publication_year": f"{now.year - 1}-{now.year}",
        }, None

    return None, None


def _run_sensor(
    root_dir: Path,
    sensor: str,
    queries: list[str],
    intent_text: str,
    identity_text: str,
    now: datetime,
) -> SensorRunResult:
    script_rel = SENSOR_SCRIPT_PATHS[sensor]
    payload, args = _sensor_payload(sensor, queries, intent_text, identity_text, now)

    if sensor == "fetch-rss" and payload and not payload.get("feeds"):
        return SensorRunResult(sensor=sensor, success=True, items=[])

    if sensor not in {"fetch-hacker-news", "fetch-github-trending", "fetch-v2ex", "fetch-product-hunt", "fetch-reddit", "fetch-rss"}:
        if not payload or not payload.get("queries"):
            return SensorRunResult(sensor=sensor, success=True, items=[])

    data, stderr = _run_json_script(root_dir, script_rel, payload=payload, args=args)
    items = data.get("items") if isinstance(data.get("items"), list) else []
    success = bool(data.get("success", False))
    error = data.get("error", "")
    if stderr and not success:
        error = f"{error}; {stderr}" if error else stderr

    return SensorRunResult(sensor=sensor, success=success, items=items, error=error)


def _save_sensor_items(root_dir: Path, sensor_result: SensorRunResult) -> int:
    payload = {
        "success": sensor_result.success,
        "items": sensor_result.items,
    }
    data, _ = _run_json_script(root_dir, DB_SAVE_ITEMS_SCRIPT, payload=payload)
    return int(data.get("inserted", 0) or 0)


def _query_unanalyzed(root_dir: Path, watch_name: str) -> list[dict[str, Any]]:
    data, _ = _run_json_script(
        root_dir,
        DB_QUERY_SCRIPT,
        args=["--watch", watch_name, "--unanalyzed"],
    )
    items = data.get("items") if isinstance(data.get("items"), list) else []
    return items


def _save_analysis(
    root_dir: Path,
    watch_name: str,
    item_ids: list[int],
    report_path: str,
    item_count: int,
    lens: str,
) -> None:
    payload = {
        "watch_name": watch_name,
        "item_ids": item_ids,
        "report_path": report_path,
        "item_count": item_count,
        "lens": lens,
    }
    _run_json_script(root_dir, DB_SAVE_ANALYSIS_SCRIPT, payload=payload)


def _to_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _sorted_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(item: dict[str, Any]) -> datetime:
        for item_key in ("published_at", "fetched_at"):
            dt = _to_datetime(item.get(item_key))
            if dt is not None:
                return dt
        return datetime.min

    return sorted(items, key=key, reverse=True)


def _item_markdown_line(item: dict[str, Any]) -> str:
    title = (item.get("title") or "(untitled)").strip()
    url = item.get("url") or ""
    source = item.get("source") or "unknown"
    when = item.get("published_at") or item.get("fetched_at") or "unknown time"
    if url:
        return f"- [{title}]({url}) — `{source}` · {when}"
    return f"- {title} — `{source}` · {when}"


def _render_report(
    watch_name: str,
    lens: str,
    items: list[dict[str, Any]],
    sensor_results: list[SensorRunResult],
    now: datetime,
) -> str:
    ordered = _sorted_items(items)
    recent = ordered[:12]
    time_str = now_iso_with_tz(now)

    source_counts: dict[str, int] = {}
    for item in items:
        source = str(item.get("source") or "unknown")
        source_counts[source] = source_counts.get(source, 0) + 1

    source_summary = ", ".join(f"{key}:{value}" for key, value in sorted(source_counts.items())) or "No data"
    sensor_errors = [f"- `{r.sensor}`: {r.error or 'failed'}" for r in sensor_results if not r.success]

    if not items:
        return (
            f"# {watch_name} insights\n\n"
            f"Generated at: {time_str}\n"
            f"Lens: `{lens}`\n\n"
            "---\n\n"
            "## Run Result\n"
            "No new items were available for analysis in this run.\n\n"
            "---\n\n"
            "## Data Source Notes\n"
            + ("\n".join(sensor_errors) if sensor_errors else "- All selected sensors completed but returned no new data.")
            + "\n"
        )

    if lens == "flash_brief":
        body = "\n".join(_item_markdown_line(it) for it in recent[:5])
        return (
            f"# {watch_name} flash brief\n\n"
            f"Generated at: {time_str}\n"
            f"Lens: `{lens}`\n\n"
            "---\n\n"
            "## Top Signals\n"
            f"{body}\n\n"
            "---\n\n"
            "## Source Coverage\n"
            f"- {source_summary}\n"
        )

    if lens == "dual_take":
        positives = recent[: min(4, len(recent))]
        negatives = recent[min(4, len(recent)) : min(8, len(recent))]
        pos_text = "\n".join(_item_markdown_line(it) for it in positives) or "- No positive signals extracted."
        neg_text = "\n".join(_item_markdown_line(it) for it in negatives) or "- No obvious downside signals extracted."
        return (
            f"# {watch_name} dual take\n\n"
            f"Generated at: {time_str}\n"
            f"Lens: `{lens}`\n\n"
            "---\n\n"
            "## Bull Case\n"
            f"{pos_text}\n\n"
            "---\n\n"
            "## Bear Case\n"
            f"{neg_text}\n\n"
            "---\n\n"
            "## Source Coverage\n"
            f"- {source_summary}\n"
        )

    if lens == "timeline_trace":
        timeline = "\n".join(_item_markdown_line(it) for it in recent)
        return (
            f"# {watch_name} timeline trace\n\n"
            f"Generated at: {time_str}\n"
            f"Lens: `{lens}`\n\n"
            "---\n\n"
            "## Timeline\n"
            f"{timeline}\n\n"
            "---\n\n"
            "## Source Coverage\n"
            f"- {source_summary}\n"
        )

    key_findings = "\n".join(_item_markdown_line(it) for it in recent[:5])
    trend_notes = []
    if source_counts:
        strongest = max(source_counts.items(), key=lambda x: x[1])
        trend_notes.append(f"- Highest signal density comes from `{strongest[0]}` ({strongest[1]} items).")
    trend_notes.append(f"- Total analyzed items this run: {len(items)}.")
    if sensor_errors:
        trend_notes.append(f"- {len(sensor_errors)} sensor(s) failed and may create coverage gaps.")

    return (
        f"# {watch_name} insights\n\n"
        f"Generated at: {time_str}\n"
        f"Lens: `{lens}`\n\n"
        "---\n\n"
        "## Key Findings\n"
        f"{key_findings}\n\n"
        "---\n\n"
        "## Trend Snapshot\n"
        + "\n".join(trend_notes)
        + "\n\n---\n\n"
        "## Action Suggestions\n"
        "1. Validate the top two signals against primary sources before acting.\n"
        "2. Confirm which noisy source should be filtered in the next run.\n"
        "3. If this theme is accelerating, switch to `timeline_trace` next cycle.\n\n"
        "---\n\n"
        "## Source Coverage\n"
        f"- {source_summary}\n"
    )


def _signal_terms(intent_text: str) -> list[str]:
    tokens: list[str] = []
    for phrase in _safe_words_from_markdown(intent_text):
        for token in re.split(r"[,，/;；\s]+", phrase):
            normalized = token.strip("-:()[]{}")
            if len(normalized) >= 3:
                tokens.append(normalized.lower())
            elif has_chinese(normalized) and len(normalized) >= 2:
                tokens.append(normalized)
    dedup: list[str] = []
    for token in tokens:
        if token not in dedup:
            dedup.append(token)
    return dedup[:12]


def _detect_alerts(items: list[dict[str, Any]], intent_text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    terms = _signal_terms(intent_text)

    ranked: list[tuple[int, dict[str, Any]]] = []
    for item in items:
        score = 0
        text = f"{item.get('title', '')} {item.get('content', '')}".lower()

        if any(term in text for term in terms):
            score += 2

        source = str(item.get("source") or "")
        if source in {"news_api", "gnews", "x_twitter", "product_hunt"}:
            score += 1

        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        numeric_signals = [
            metadata.get("votes_count", 0),
            metadata.get("like_count", 0),
            metadata.get("score", 0),
            metadata.get("stars_today", 0),
        ]
        if any(isinstance(v, (int, float)) and v >= 50 for v in numeric_signals):
            score += 1

        if score >= 2:
            ranked.append((score, item))

    ranked.sort(key=lambda x: x[0], reverse=True)
    highs = [item for score, item in ranked if score >= 3][:3]
    mediums = [item for score, item in ranked if score == 2][:3]
    return highs, mediums


def _render_alert_markdown(
    watch_name: str,
    highs: list[dict[str, Any]],
    mediums: list[dict[str, Any]],
    now: datetime,
) -> str:
    lines = [
        f"# {watch_name} alert",
        "",
        f"Generated at: {now_iso_with_tz(now)}",
        "",
        "---",
        "",
    ]

    for level, level_items in (("High", highs), ("Medium", mediums)):
        for item in level_items:
            title = item.get("title") or "(untitled)"
            source = item.get("source") or "unknown"
            url = item.get("url") or ""
            lines.extend(
                [
                    f"## [{level}] {title}",
                    "",
                    f"- **Source**: {source}",
                    f"- **Link**: {url}" if url else "- **Link**: (none)",
                    "- **Reason**: Strong alignment with watch intent and elevated source signal.",
                    "",
                    "---",
                    "",
                ]
            )

    return "\n".join(lines).rstrip() + "\n"


def update_watch_state(state_path: Path, now: datetime | None = None) -> dict[str, Any]:
    """Update watch state.json last_run with timezone-aware ISO timestamp."""
    current = now or datetime.now().astimezone()
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            state = {}
    else:
        state = {}

    state.setdefault("check_interval", "1d")
    state.setdefault("status", "active")
    state["last_run"] = now_iso_with_tz(current)

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return state


def run_watch(
    root_dir: Path,
    watch_name: str,
    lens_override: str | None = None,
    since: str | None = None,
) -> dict[str, Any]:
    """Execute one watch cycle using existing skill scripts as runtime primitives."""
    root = root_dir.resolve()
    watch_dir = root / "watches" / watch_name
    intent_path = watch_dir / "intent.md"
    memory_path = watch_dir / "memory.md"
    state_path = watch_dir / "state.json"

    if not watch_dir.exists() or not intent_path.exists():
        raise FileNotFoundError(f"Watch '{watch_name}' not found at {watch_dir}")

    intent_text = read_text(intent_path)
    memory_text = read_text(memory_path)
    identity_text = read_text(root / "profile/identity.md")

    selected_sensors = select_sensors(intent_text, memory_text)
    lens = infer_lens(memory_text, override=lens_override)
    now = datetime.now().astimezone()
    queries = generate_search_queries(watch_name, intent_text, memory_text, now=now)

    sensor_results: list[SensorRunResult] = []
    inserted_items = 0

    for sensor in selected_sensors:
        result = _run_sensor(root, sensor, queries, intent_text, identity_text, now)
        result.inserted = _save_sensor_items(root, result)
        inserted_items += result.inserted
        sensor_results.append(result)

    items = _query_unanalyzed(root, watch_name)
    if since:
        threshold = _to_datetime(since)
        if threshold:
            filtered = []
            for item in items:
                fetched = _to_datetime(item.get("fetched_at"))
                if fetched and fetched >= threshold:
                    filtered.append(item)
            items = filtered

    report_markdown = _render_report(watch_name, lens, items, sensor_results, now)

    date_dir = now.strftime("%Y-%m-%d")
    report_dir = root / "reports" / date_dir / watch_name
    report_dir.mkdir(parents=True, exist_ok=True)

    report_path = report_dir / "insights.md"
    report_path.write_text(report_markdown, encoding="utf-8")

    raw_path = report_dir / "raw_intel.md"
    raw_lines = [
        f"# {watch_name} raw intel",
        "",
        f"Generated at: {now_iso_with_tz(now)}",
        "",
        "---",
        "",
    ]
    for item in _sorted_items(items)[:50]:
        raw_lines.append(_item_markdown_line(item))
    if len(raw_lines) <= 7:
        raw_lines.append("- No unanalyzed items in this cycle.")
    raw_path.write_text("\n".join(raw_lines).rstrip() + "\n", encoding="utf-8")

    highs, mediums = _detect_alerts(items, intent_text)
    alert_rel_path = ""
    if highs or mediums:
        alert_dir = root / "alerts" / date_dir
        alert_dir.mkdir(parents=True, exist_ok=True)
        alert_path = alert_dir / f"{watch_name}.md"
        alert_path.write_text(_render_alert_markdown(watch_name, highs, mediums, now), encoding="utf-8")
        alert_rel_path = str(alert_path.relative_to(root))

    item_ids = [int(item["id"]) for item in items if isinstance(item.get("id"), int)]
    report_rel_path = str(report_path.relative_to(root))
    _save_analysis(root, watch_name, item_ids, report_rel_path, len(items), lens)
    update_watch_state(state_path, now=now)

    return {
        "success": True,
        "watch": watch_name,
        "selected_sensors": selected_sensors,
        "inserted_items": inserted_items,
        "analyzed_items": len(items),
        "report_path": report_rel_path,
        "alert_path": alert_rel_path,
        "lens": lens,
        "sensor_errors": [
            {"sensor": r.sensor, "error": r.error} for r in sensor_results if not r.success and r.error
        ],
    }
