---
name: fetch-hacker-news
description: 从 Hacker News 获取热门技术资讯。用于监控技术趋势、开发者工具、开源项目、创业动态等方向。当 Watch intent 涉及英语技术社区信号时使用。
---

# fetch-hacker-news

运行脚本获取 HN 热门文章：

```bash
uv run python .claude/skills/fetch-hacker-news/scripts/fetch.py [--max-items 30]
```

脚本输出 JSON 到 stdout，包含 items 数组。每个 item 有 title, url, score,
descendants(评论数), author, published_at。

无需 API key。使用 Firebase 公开 API。
