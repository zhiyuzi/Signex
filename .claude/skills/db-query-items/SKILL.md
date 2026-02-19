---
name: db-query-items
description: 从数据库查询数据项。支持按 watch 查询未分析项、按来源筛选、按时间筛选。
---

# db-query-items 查询数据

```bash
uv run python .claude/skills/db-query-items/scripts/query.py --watch ai-coding-tools --unanalyzed
uv run python .claude/skills/db-query-items/scripts/query.py --source hacker_news --since 2026-02-10
```

参数：
- `--watch NAME` + `--unanalyzed`：获取该 watch 未分析的项目
- `--source NAME`：按来源筛选
- `--since TIMESTAMP`：起始时间（ISO 8601）
- `--until TIMESTAMP`：结束时间（ISO 8601）

输出 JSON：`{"success": true, "items": [...], "count": N}`
