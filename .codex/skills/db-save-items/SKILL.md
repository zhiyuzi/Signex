---
name: db-save-items
description: 将采集到的数据项保存到 SQLite 数据库。Sensor 采集完数据后使用。自动去重（基于 source + source_id）。
---

# db-save-items 保存数据

从 stdin 读取 Sensor 输出的 JSON，将 items 保存到数据库：

```bash
echo '{"items": [...]}' | uv run python .claude/skills/db-save-items/scripts/save.py
```

或直接管道连接 Sensor 输出：

```bash
uv run python .claude/skills/fetch-hacker-news/scripts/fetch.py | uv run python .claude/skills/db-save-items/scripts/save.py
```

输出 JSON：`{"success": true, "inserted": N, "total": M}`

自动去重：相同 (source, source_id) 不会重复插入。
