---
name: fetch-arxiv
description: 从 arXiv 获取学术预印本。支持按关键词、分类（cs.AI, cs.CL 等）搜索最新论文。完全免费，无需 API key。当 Watch intent 涉及前沿研究、学术趋势、技术论文时使用。
---

# fetch-arxiv

通过 arXiv API 搜索学术预印本，返回标准 JSON 格式。

```bash
echo '{"queries": ["LLM agent planning"], "categories": ["cs.AI", "cs.CL"], "max_results": 20}' | uv run python .claude/skills/fetch-arxiv/scripts/search.py
```

参数：
- `queries`: 搜索查询词数组（必填）
- `categories`: arXiv 分类过滤（可选，如 `["cs.AI", "cs.CL"]`）
- `max_results`: 每个查询返回结果数（默认 20，最大 100）
- `sort_by`: 排序 — `submittedDate`（默认）、`relevance`、`lastUpdatedDate`
- `sort_order`: 排序方向 — `descending`（默认）、`ascending`

常用 arXiv 分类：
- `cs.AI` — 人工智能
- `cs.CL` — 计算语言学 / NLP
- `cs.SE` — 软件工程
- `cs.LG` — 机器学习
- `cs.CV` — 计算机视觉
- `cs.CR` — 密码学与安全
- `cs.DC` — 分布式计算
- `stat.ML` — 统计机器学习

无需 API key。礼貌策略：请求间隔 ≥ 3 秒。
