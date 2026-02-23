---
name: fetch-v2ex
description: 从 V2EX 获取热门话题。用于监控中文技术社区动态、开发者讨论、产品反馈等。当 Watch intent 涉及中文技术社区信号时使用。
---

# fetch-v2ex

运行脚本获取 V2EX 热门话题：

```bash
uv run python .claude/skills/fetch-v2ex/scripts/fetch.py
```

脚本输出 JSON 到 stdout。每个 item 有 title, url, content, node, replies, member。

无需 API key。使用 V2EX 公开 API。
