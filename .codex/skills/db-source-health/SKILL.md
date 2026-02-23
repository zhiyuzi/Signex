---
name: db-source-health
description: 查询各数据源的健康状态。显示每个 source 的最近成功/失败时间、连续失败次数、总调用次数和失败率。用于开场交互时检查源健康。
---

# db-source-health 源健康状态

查询各数据源的健康状态：

```bash
uv run python .claude/skills/db-source-health/scripts/health.py
```

输出 JSON：
```json
{
  "success": true,
  "sources": [
    {
      "source": "hacker_news",
      "last_success": "2026-02-19T...",
      "last_failure": null,
      "consecutive_failures": 0,
      "total_calls": 15,
      "total_failures": 1,
      "failure_rate": 0.067
    }
  ],
  "unhealthy": ["x_twitter"],
  "total_sources": 5
}
```

`unhealthy` 列表包含连续失败 >= 3 次的源，用于快速判断是否需要关注。
