---
name: fetch-product-hunt
description: 从 Product Hunt GraphQL API 获取最新产品发布。用于发现新产品趋势、创业动态。当 Watch intent 涉及新产品发布、产品趋势时使用。需要 PRODUCTHUNT_ACCESS_TOKEN 环境变量。
---

# fetch-product-hunt

运行脚本获取 Product Hunt 最新产品：

```bash
uv run python .claude/skills/fetch-product-hunt/scripts/fetch.py [--limit 20] [--featured] [--topic ai] [--after 2026-02-01]
```

参数：
- `--limit`: 获取数量（默认 20）
- `--featured`: 仅获取 featured posts
- `--topic`: 按话题筛选（如 ai, developer-tools）
- `--after`: 仅获取此日期之后的 posts（ISO 格式）

需要环境变量 `PRODUCTHUNT_ACCESS_TOKEN`（从 https://www.producthunt.com/v2/oauth/applications 获取）。

脚本输出 JSON 到 stdout，包含 items 数组。每个 item 有 title, url, tagline, votes_count, comments_count, topics, featured_at, website。
