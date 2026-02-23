---
name: fetch-tavily
description: 通过 Tavily API 进行定向网络搜索。用于根据 Watch intent 生成的搜索查询词获取最新信息。需要 TAVILY_API_KEY 环境变量。当需要搜索特定话题的最新信息时使用。
---

# fetch-tavily

从 stdin 读取 JSON 参数，运行 Tavily 搜索：

```bash
echo '{"queries": ["query1", "query2"], "days": 7}' | uv run python .claude/skills/fetch-tavily/scripts/search.py
```

参数：
- `queries`: 搜索查询词数组
- `days`: 时间窗口（天数，默认 7）

需要环境变量 `TAVILY_API_KEY`（从项目 .env 文件加载）。

脚本输出 JSON 到 stdout，包含去重后的搜索结果。按 URL 去重，保留相关性评分更高的结果。
