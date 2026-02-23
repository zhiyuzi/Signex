# Runtime Compatibility (Claude + Codex)

This document defines how Signex runs in both Claude Code and Codex with a discoverable Codex skill mirror.

## Design Choice

- Keep `.claude/skills/` as the source-of-truth skill tree.
- Mirror `.claude/skills/` to `.codex/skills/` for Codex-native skill discovery.
- Use `./scripts/sync-codex-skills` to refresh the mirror.
- Add a lightweight Codex runtime layer under `src/runtime/`.
- Keep `CLAUDE.md` for Claude behavior and add `AGENTS.md` for Codex behavior.

## Execution Mapping

| Capability | Claude Flow | Codex Flow |
|---|---|---|
| Initialize workspace | `/init` command | `signex init` |
| Greeting / daily briefing | natural-language “Hi” | `signex hi` (or NL routed to it) |
| Run one watch | `run-watch` skill orchestration | `signex run --watch <name>` |
| Save items to DB | `db-save-items` skill | same script invoked by runtime |
| Query unanalyzed items | `db-query-items` skill | same script invoked by runtime |
| Save analysis record | `db-save-analysis` skill | same script invoked by runtime |

## Runtime Modules

- `src/runtime/init_workspace.py`: idempotent initialization logic
- `src/runtime/router.py`: natural-language intent routing
- `src/runtime/briefing.py`: status summary builder for greeting
- `src/runtime/watch_runner.py`: watch orchestration over existing scripts
- `src/runtime/cli.py`: unified entrypoint (`signex`)

## Command Contract

```bash
signex init
signex hi [--json]
signex route "<message>"
signex run --watch <name> [--lens deep_insight|flash_brief|dual_take|timeline_trace] [--since <ISO8601>]
signex stats
```

## Guardrails

- Edit skills under `.claude/skills/` first, then sync to `.codex/skills/`.
- Do not hand-edit `.codex/skills/` unless you know the sync impact.
- No behavior rewrite in sensor/lens/db scripts unless intentionally needed.
