---
name: db-save-items
description: 将采集到的数据项保存到 SQLite 数据库。Sensor 采集完数据后使用。自动去重（基于 source + source_id）。
---

# db-save-items 保存数据

从 stdin 读取 Sensor 输出的 JSON，将 items 保存到数据库。支持 `watch_name` 标记数据归属。

```bash
echo '{"items": [...], "watch_name": "product-opportunities"}' | uv run python .claude/skills/db-save-items/scripts/save.py
```

或直接管道连接 Sensor 输出（注意：管道模式无法传 watch_name，需要在调用前合并 JSON）：

```bash
uv run python .claude/skills/fetch-hacker-news/scripts/fetch.py | uv run python .claude/skills/db-save-items/scripts/save.py
```

输出 JSON：
```json
{
  "success": true,
  "inserted": 5,
  "total": 10,
  "item_ids": [1, 2, 3],
  "summary": [
    {"source": "...", "title": "...", "content": "前150字...", "url": "..."}
  ]
}
```

- `item_ids`：本次新插入的 item ID 列表，用于后续 `db-save-analysis` 标记
- `summary`：所有 items 的精简版（仅 source/title/content 前 150 字/url），供 LLM 分析用，省 token
- 自动去重：相同 (source, source_id) 不会重复插入
- `watch_name`：可选，标记这批数据是哪个 watch 采集的
