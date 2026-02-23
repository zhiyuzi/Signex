---
name: fetch-rss
description: 通用 RSS/Atom 解析器。一个 skill 覆盖任意 feed，Claude 根据 intent/memory 自主决定传入哪些 feed URL。用于监控官方博客、changelog、长尾信息源。无需 API key。
---

# fetch-rss

从 stdin 读取 JSON 参数，解析 RSS/Atom feeds：

```bash
echo '{"feeds": ["https://blog.cursor.com/rss.xml", "https://simonwillison.net/atom/everything/"], "max_per_feed": 20}' | uv run python .claude/skills/fetch-rss/scripts/fetch.py
```

参数：
- `feeds`: RSS/Atom feed URL 数组
- `max_per_feed`: 每个 feed 最多获取条目数（默认 20）

无需 API key。使用 feedparser 库解析 RSS 2.0、Atom、RDF 格式。

脚本输出 JSON 到 stdout，包含所有 feed 的合并结果。单个 feed 失败不影响其他，失败的 feed URL 记录在 error 字段。
