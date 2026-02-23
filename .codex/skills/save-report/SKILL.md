---
name: save-report
description: 保存分析报告和高信号警报。生成报告后使用，将报告写入 reports/ 目录，将警报写入 alerts/ 目录。
---

# save-report 保存报告

## 报告保存
将分析报告保存到 `reports/{YYYY-MM-DD}/{watch-name}/insights.md`。

使用 Write 工具创建文件。目录不存在时会自动创建。

## 可选：原始情报
如果有原始数据汇总，保存到 `reports/{YYYY-MM-DD}/{watch-name}/raw_intel.md`。

## 高信号警报
在分析过程中，如果发现对该 Watch 的 intent 特别重要的内容（高信号），
同时输出警报文件到 `alerts/{YYYY-MM-DD}/{watch-name}.md`。

### 警报格式

```markdown
# {watch-name} 警报

生成时间: {ISO 8601 timestamp}

---

## [高] {title}

- **来源**: {source}
- **链接**: {url}
- **重要性**: {reason}

---

## [中] {title}

...
```

### 警报严重级别
- **高**：直接命中 Watch intent 核心关注点
- **中**：与 intent 相关但非核心

### 判断标准
不使用关键词过滤。在分析数据的过程中，结合该 Watch 的 intent.md 和
memory.md，自然地识别哪些内容特别重要。每个 Watch 的"重要"标准不同，
由其 intent 决定。
