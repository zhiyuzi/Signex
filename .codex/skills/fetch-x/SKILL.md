---
name: fetch-x
description: 通过 X/Twitter API v2 搜索最近推文。用于获取实时社交信号、产品发布动态。Free tier 限制 1500 reads/月，仅搜索最近 7 天。需要 X_BEARER_TOKEN 环境变量。注意：数据不得用于模型训练。
---

# fetch-x

从 stdin 读取 JSON 参数，搜索 X/Twitter 最近推文：

```bash
echo '{"queries": ["AI IDE", "Cursor update"], "max_results": 10, "min_likes": 5}' | uv run python .claude/skills/fetch-x/scripts/search.py
```

参数：
- `queries`: 搜索查询词数组
- `max_results`: 每个查询返回结果数（默认 10，最大 10）
- `min_likes`: 最低点赞数过滤（默认 0，建议 3-10，由 AI 根据话题热度动态决定）
- `min_retweets`: 最低转发数过滤（默认 0）

费用提示：按量计费，约 $0.005/条推文。建议每次 1-2 个 query，max_results 保持 10，配合 min_likes 过滤低质量内容。

需要环境变量 `X_BEARER_TOKEN`（从项目 .env 文件加载）。

脚本输出 JSON 到 stdout，包含去重后的推文。按 tweet id 去重。

合规提示：数据仅用于个人情报分析，不得用于模型训练。
