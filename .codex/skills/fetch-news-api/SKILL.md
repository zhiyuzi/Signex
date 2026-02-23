---
name: fetch-news-api
description: 通过 NewsAPI.org 搜索新闻报道。用于获取行业动态、新闻报道。Free tier 100 requests/天，结果有 24h 延迟。需要 NEWS_API_KEY 环境变量。
---

# fetch-news-api

从 stdin 读取 JSON 参数，搜索新闻报道：

```bash
echo '{"queries": ["AI developer tools"], "days": 7, "language": "en", "sort_by": "relevancy"}' | uv run python .claude/skills/fetch-news-api/scripts/search.py
```

参数：
- `queries`: 搜索查询词数组
- `days`: 时间窗口天数（默认 7）
- `language`: 语言代码（默认 "en"）
- `sort_by`: 排序方式 relevancy/popularity/publishedAt（默认 "relevancy"）

需要环境变量 `NEWS_API_KEY`（从项目 .env 文件加载）。

脚本输出 JSON 到 stdout，包含去重后的新闻结果。按 URL 去重。
