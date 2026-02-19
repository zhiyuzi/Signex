---
name: db-save-analysis
description: 记录分析运行到数据库。每次 Watch 分析完成后使用，记录 watch 名、运行时间、分析的 item 数量、使用的 lens、报告路径。
---

# db-save-analysis 记录分析

从 stdin 读取分析记录 JSON：

```bash
echo '{"watch_name": "ai-coding-tools", "item_ids": [1,2,3], "report_path": "reports/2026-02-17/ai-coding-tools/insights.md", "item_count": 45, "lens": "deep_insight"}' | uv run python .claude/skills/db-save-analysis/scripts/save.py
```

输出：`{"success": true, "analysis_id": N}`
