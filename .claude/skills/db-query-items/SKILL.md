---
name: db-query-items
description: 从数据库查询数据项。支持按 watch、来源、时间范围筛选。
---

# db-query-items 查询数据

```bash
uv run python .claude/skills/db-query-items/scripts/query.py --watch product-opportunities
uv run python .claude/skills/db-query-items/scripts/query.py --source hacker_news --since 2026-02-10
```

参数：
- `--watch NAME`：按 watch 名称筛选
- `--source NAME`：按来源筛选
- `--since TIMESTAMP`：起始时间（ISO 8601）
- `--until TIMESTAMP`：结束时间（ISO 8601）

输出 JSON：`{"success": true, "items": [...], "count": N}`
