---
name: lens-deep-insight
description: 综合情报分析视角。生成包含关键发现、趋势分析和行动建议的深度报告。这是默认的分析视角，适用于大多数情况。当用户未指定 lens 时使用。
---

# lens-deep-insight 深度洞察

## 使用场景
默认分析视角。综合分析采集到的数据，输出结构化的深度报告。

## 分析方法
1. 读取 `references/prompt-template.md` 中的分析框架
2. 将采集到的数据项作为输入
3. 结合 Watch 的 intent.md 和 memory.md
4. 按模板框架生成分析报告

## 输出
Markdown 格式报告，保存到 `reports/{date}/{watch-name}/insights.md`
