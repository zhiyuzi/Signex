"""Unified Signex runtime CLI for Claude/Codex compatibility."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from src.runtime.briefing import build_briefing
from src.runtime.init_workspace import ensure_initialized
from src.runtime.router import route_message
from src.runtime.watch_runner import run_watch
from src.store.database import Database


def _root_from_args(path_arg: str | None) -> Path:
    if path_arg:
        return Path(path_arg).resolve()
    return Path.cwd().resolve()


def _critical_files_ready(root_dir: Path) -> bool:
    required = [
        root_dir / "profile/identity.md",
        root_dir / "watches/index.md",
        root_dir / "vault/index.md",
    ]
    return all(path.exists() for path in required)


def _print_json(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_init(args: argparse.Namespace) -> int:
    root = _root_from_args(args.root)
    summary = ensure_initialized(root)

    if args.json:
        _print_json({"success": True, **summary.to_dict()})
    else:
        print("Signex initialized.")
        print(f"- Created dirs: {len(summary.created_dirs)}")
        print(f"- Created files: {len(summary.created_files)}")
        if summary.env_missing:
            print("- .env is missing. Copy .env.example to .env and fill API keys.")
    return 0


def cmd_hi(args: argparse.Namespace) -> int:
    root = _root_from_args(args.root)
    if not _critical_files_ready(root):
        ensure_initialized(root)

    text, payload = build_briefing(root)
    if args.json:
        _print_json({"success": True, "briefing": text, **payload})
    else:
        print(text)
    return 0


def cmd_route(args: argparse.Namespace) -> int:
    result = route_message(args.text)
    _print_json(result.to_dict())
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    root = _root_from_args(args.root)
    if not _critical_files_ready(root):
        ensure_initialized(root)

    result = run_watch(
        root_dir=root,
        watch_name=args.watch,
        lens_override=args.lens,
        since=args.since,
    )

    if args.json:
        _print_json(result)
    else:
        print(f"Watch `{result['watch']}` completed.")
        print(f"- Sensors: {', '.join(result['selected_sensors'])}")
        print(f"- Inserted: {result['inserted_items']}")
        print(f"- Analyzed: {result['analyzed_items']}")
        print(f"- Report: {result['report_path']}")
        if result.get("alert_path"):
            print(f"- Alert: {result['alert_path']}")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    root = _root_from_args(args.root)
    db = Database(str(root / "data/signex.db"))
    db.init()
    try:
        payload = db.get_run_stats()
    finally:
        db.close()

    _print_json({"success": True, **payload})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="signex", description="Signex dual-runtime helper CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    init_cmd = sub.add_parser("init", help="Idempotently initialize workspace")
    init_cmd.add_argument("--root", help="Project root path (default: cwd)")
    init_cmd.add_argument("--json", action="store_true", help="Output JSON")
    init_cmd.set_defaults(func=cmd_init)

    hi_cmd = sub.add_parser("hi", help="Show a short situational briefing")
    hi_cmd.add_argument("--root", help="Project root path (default: cwd)")
    hi_cmd.add_argument("--json", action="store_true", help="Output JSON")
    hi_cmd.set_defaults(func=cmd_hi)

    route_cmd = sub.add_parser("route", help="Classify one user utterance")
    route_cmd.add_argument("text", help="Input user message")
    route_cmd.set_defaults(func=cmd_route)

    run_cmd = sub.add_parser("run", help="Run a watch cycle")
    run_cmd.add_argument("--watch", required=True, help="Watch name")
    run_cmd.add_argument("--lens", choices=["deep_insight", "flash_brief", "dual_take", "timeline_trace"])
    run_cmd.add_argument("--since", help="Optional ISO8601 lower bound for analysis items")
    run_cmd.add_argument("--root", help="Project root path (default: cwd)")
    run_cmd.add_argument("--json", action="store_true", help="Output JSON")
    run_cmd.set_defaults(func=cmd_run)

    stats_cmd = sub.add_parser("stats", help="Show run statistics from SQLite")
    stats_cmd.add_argument("--root", help="Project root path (default: cwd)")
    stats_cmd.set_defaults(func=cmd_stats)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
