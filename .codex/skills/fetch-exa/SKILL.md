---
name: fetch-exa
description: 通过 Exa AI 语义搜索获取深度内容。与 Tavily 互补：Exa 擅长语义相似度搜索，Tavily 擅长时效性关键词搜索。需要 EXA_API_KEY 环境变量。
---

# fetch-exa

使用 Exa AI SDK 进行语义搜索，自动获取 highlights（关键摘录）和 text（正文片段）。

```bash
echo '{"queries": ["AI native IDE tools"], "num_results": 10, "days": 7}' | uv run python .claude/skills/fetch-exa/scripts/search.py
```

参数：
- `queries`: 搜索查询词数组（支持自然语言语义查询，如 "tools that help developers write code faster"）
- `num_results`: 每个查询返回结果数（默认 10）
- `days`: 时间窗口天数（默认 7）
- `category`: 可选，内容类别过滤（如 "research paper", "news", "blog post", "company", "tweet" 等）
- `include_domains`: 可选，只搜索这些域名（如 `["arxiv.org", "github.com"]`）
- `exclude_domains`: 可选，排除这些域名

需要环境变量 `EXA_API_KEY`（从项目 .env 文件加载）。

搜索类型自动选择（`type="auto"`），Exa 根据查询内容决定最佳策略。返回结果包含 highlights（5 句关键摘录）和 text（前 1000 字正文），content 字段优先使用 highlights。按 URL 去重，保留相关性评分更高的结果。
