# Runtime Compatibility (Claude + Codex)

This document defines how Signex runs in both Claude Code and Codex without duplicating skill implementations.

## Design Choice

- Keep `.claude/skills/*/scripts` as the single execution implementation.
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

## Non-goals

- No mirror `.codex/skills/` directory.
- No rewrite of existing `.claude/skills` script internals.
