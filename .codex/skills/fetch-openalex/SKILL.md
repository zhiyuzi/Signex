---
name: fetch-openalex
description: 通过 OpenAlex API 搜索学术论文。覆盖 2.5 亿+ 学术作品，提供引用数、开放获取状态、学科分类。与 arXiv 互补：arXiv 追踪最新预印本，OpenAlex 评估论文影响力和发现跨学科关联。需要 OPENALEX_API_KEY 环境变量。
---

# fetch-openalex

通过 OpenAlex API 搜索学术论文，返回标准 JSON 格式。

```bash
echo '{"queries": ["LLM agent planning"], "per_page": 20, "publication_year": "2025-2026"}' | uv run python .claude/skills/fetch-openalex/scripts/search.py
```

参数：
- `queries`: 搜索查询词数组（必填）
- `per_page`: 每个查询返回结果数（默认 20，最大 200）
- `publication_year`: 年份过滤（可选，如 `"2026"` 或 `"2025-2026"`）
- `type`: 作品类型过滤（可选，如 `"article"`、`"preprint"`）
- `open_access_only`: 是否只返回开放获取论文（默认 false）

需要环境变量 `OPENALEX_API_KEY`（从 https://openalex.org/settings/api 免费申请）。$10/天免费预算，搜索 $1/1000 次调用。

返回结果包含引用数、开放获取状态、学科主题、DOI、作者机构等元数据。按 OpenAlex Work ID 去重，保留引用数更高的结果。
