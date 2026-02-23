---
name: fetch-reddit
description: 从 Reddit 公开 JSON API 获取热门帖子和搜索结果。用于监控社区讨论、用户反馈、痛点。当 Watch intent 涉及社区讨论、用户反馈时使用。无需 API key。
---

# fetch-reddit

从 stdin 读取 JSON 参数，获取 Reddit 帖子：

列表模式：
```bash
echo '{"subreddits": ["SaaS", "startups", "programming"], "sort": "hot", "limit": 25}' | uv run python .claude/skills/fetch-reddit/scripts/fetch.py
```

搜索模式：
```bash
echo '{"search": "AI coding tools", "subreddit": "programming", "sort": "relevance", "time": "week", "limit": 25}' | uv run python .claude/skills/fetch-reddit/scripts/fetch.py
```

参数（列表模式）：
- `subreddits`: subreddit 名称数组
- `sort`: 排序方式（hot, new, top，默认 hot）
- `limit`: 每个 subreddit 获取数量（默认 25）

参数（搜索模式）：
- `search`: 搜索关键词
- `subreddit`: 在哪个 subreddit 搜索
- `sort`: 排序（relevance, hot, top, new，默认 relevance）
- `time`: 时间范围（hour, day, week, month, year, all，默认 week）
- `limit`: 返回数量（默认 25）

无需 API key。使用 Reddit 公开 JSON API（100 QPM 限制）。

脚本输出 JSON 到 stdout。每个 item 有 title, url, selftext, score, num_comments, author, subreddit, upvote_ratio。
