---
name: fetch-gnews
description: 通过 GNews API 搜索新闻。与 NewsAPI 互补，支持更多语言和地区筛选。Free tier 100 requests/天，10 articles/request。需要 GNEWS_API_KEY 环境变量。
---

# fetch-gnews

从 stdin 读取 JSON 参数，搜索新闻：

```bash
echo '{"queries": ["AI tools"], "max_results": 10, "language": "en"}' | uv run python .claude/skills/fetch-gnews/scripts/search.py
```

参数：
- `queries`: 搜索查询词数组
- `max_results`: 每个查询返回结果数（默认 10，最大 10）
- `language`: 语言代码（默认 "en"）

需要环境变量 `GNEWS_API_KEY`（从项目 .env 文件加载）。

脚本输出 JSON 到 stdout，包含去重后的新闻结果。按 URL 去重。
