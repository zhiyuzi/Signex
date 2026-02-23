# Codex Skill Mirror

`.codex/skills/` and `.codex/commands/` are mirrored from `.claude/` so Codex can discover the same skills.

- Source of truth: `.claude/skills/` and `.claude/commands/`
- Sync command: `./scripts/sync-codex-skills`

Avoid editing mirrored files manually unless you also update the source tree.
