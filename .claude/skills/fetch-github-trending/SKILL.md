---
name: fetch-github-trending
description: 从 GitHub Trending 页面获取热门仓库。用于发现新兴开源项目、技术趋势。当 Watch intent 涉及开源生态或技术工具时使用。
---

# fetch-github-trending

运行脚本获取 GitHub Trending 热门仓库：

```bash
uv run python .claude/skills/fetch-github-trending/scripts/fetch.py
```

脚本输出 JSON 到 stdout。每个 item 有 repo name, description, language,
stars_today, total_stars。

无需 API key。使用网页抓取。
