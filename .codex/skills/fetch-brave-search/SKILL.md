---
name: fetch-brave-search
description: 通过 Brave Search API 进行网络搜索。作为 Tavily 的备选/补充搜索源，使用独立索引（不依赖 Google）。2000 requests/月免费。需要 BRAVE_API_KEY 环境变量。
---

# fetch-brave-search

从 stdin 读取 JSON 参数，运行 Brave Search：

```bash
echo '{"queries": ["query1", "query2"], "count": 10}' | uv run python .claude/skills/fetch-brave-search/scripts/search.py
```

参数：
- `queries`: 搜索查询词数组
- `count`: 每个查询返回的结果数量（默认 10）

需要环境变量 `BRAVE_API_KEY`（从项目 .env 文件加载）。

费用提示：$5/1000 requests（每月 $5 免费额度）。硬限制每次最多返回 10 条结果。建议每次 1-2 个 query，仅在 Tavily 不可用或需要交叉验证搜索结果时使用。

脚本输出 JSON 到 stdout，包含去重后的搜索结果。按 URL 去重，保留首次出现的结果。
