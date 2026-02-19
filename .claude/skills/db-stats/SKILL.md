---
name: db-stats
description: 输出运行历史统计。显示各 Watch 运行次数、采集 item 数、最近运行时间、按日期分布等。
---

# db-stats 运行统计

```bash
uv run python .claude/skills/db-stats/scripts/stats.py
```

输出 JSON，包含：
- by_watch: 各 watch 的运行次数、item 总数、最近运行、使用的 lens 类型
- by_date: 按日期的运行分布
- totals: 总运行次数和 item 总数
