---
name: fetch-request-hunt
description: 通过 RequestHunt API 搜索用户功能请求和痛点。用于发现产品机会、用户需求趋势。当 Watch intent 涉及用户需求、功能请求、痛点挖掘时使用。需要 REQUESTHUNT_API_KEY 环境变量。
---

# fetch-request-hunt

从 stdin 读取 JSON 参数，搜索 RequestHunt 功能请求：

```bash
echo '{"queries": ["AI IDE feature requests"], "limit": 20}' | uv run python .claude/skills/fetch-request-hunt/scripts/search.py
```

参数：
- `queries`: 搜索查询词数组
- `limit`: 每个查询返回数量（默认 20）
- `expand`: 是否实时抓取详情（默认 false，使用缓存节省配额）

需要环境变量 `REQUESTHUNT_API_KEY`（从 https://requesthunt.com/settings/api 获取）。

脚本输出 JSON 到 stdout，包含去重后的搜索结果。每个 item 有 title, url, description, votes, comment_count, topic, source_platform。
