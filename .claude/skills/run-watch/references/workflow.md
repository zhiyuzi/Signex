# run-watch 决策树

## Sensor 选择决策

根据 Watch intent 中的关键词和方向选择 Sensor：

| Intent 关键特征 | 推荐 Sensor |
|-----------------|-------------|
| 英语技术社区、开发者工具、创业 | fetch-hacker-news |
| 开源项目、GitHub、技术工具 | fetch-github-trending |
| 中文社区、国内技术、产品反馈 | fetch-v2ex |
| 需要定向搜索特定话题 | fetch-tavily |

**原则**：宁可少调不调多。每个 Sensor 都有成本（时间、API 配额）。
如果 intent 明确聚焦某个方向，只调相关的 1-2 个 Sensor。

## 搜索词生成（fetch-tavily）

当使用 fetch-tavily 时，需要根据 intent 生成搜索词：

1. 提取 intent 中的核心关注点（3-5 个）
2. 为每个关注点生成 1-2 个搜索查询
3. **每个查询必须包含年月**（如 "2026-02"）
4. 参考 memory.md 中的排除项，避免搜索已排除的内容
5. 混合中英文查询以获得更好的覆盖

示例（ai-coding-tools watch）：
```json
{
  "queries": [
    "AI native IDE 2026-02 new release",
    "Cursor AI IDE update February 2026",
    "Claude Code 新功能 2026年2月",
    "AI coding assistant 2026-02 comparison",
    "AI编程工具 最新动态 2026-02"
  ],
  "days": 7
}
```

## Lens 选择决策

| 场景 | 推荐 Lens |
|------|-----------|
| 常规分析（默认） | deep_insight |
| 用户要求快速了解 | flash_brief |
| 评估某个产品/技术 | dual_take |
| 跟踪事件发展 | timeline_trace |
| memory.md 中有 lens 偏好 | 按偏好 |

## 高信号识别

在分析过程中自然识别，不使用关键词过滤。判断标准：
- 直接命中 intent 核心关注点 → 高
- 与 intent 相关的重要信息 → 中
- 背景信息 → 不生成 alert

## 异常处理

- **Sensor 失败**：跳过该 Sensor，继续其他。在报告中注明数据缺口。
- **无数据**：生成简短报告说明"本次无新数据"，仍更新 last_run。
- **API key 缺失**：跳过需要 key 的 Sensor，使用可用的免费 Sensor。

## 完整执行示例

```
用户："运行 ai-coding-tools watch"

1. 读取 watches/ai-coding-tools/intent.md → 关注 AI 编程工具
   读取 watches/ai-coding-tools/memory.md → 聚焦 Claude Code，排除 Windsurf
   读取 watches/ai-coding-tools/state.json → 上次运行 2026-02-15
   读取 profile/identity.md → 用户偏好中文报告

2. 选择 Sensor：
   - fetch-hacker-news ✅（英语技术社区）
   - fetch-github-trending ✅（开源项目）
   - fetch-v2ex ✅（中文社区）
   - fetch-tavily ✅（定向搜索 Claude Code 等）

3. 执行采集：
   $ uv run python .claude/skills/fetch-hacker-news/scripts/fetch.py
   $ uv run python .claude/skills/fetch-github-trending/scripts/fetch.py
   $ uv run python .claude/skills/fetch-v2ex/scripts/fetch.py
   $ echo '{"queries": [...], "days": 7}' | uv run python .claude/skills/fetch-tavily/scripts/search.py

4. 每个 Sensor 输出通过管道传给 db-save-items 保存

5. 查询未分析数据：
   $ uv run python .claude/skills/db-query-items/scripts/query.py --watch ai-coding-tools --unanalyzed

6. 选择 lens（memory 无偏好，默认 deep_insight）
   读取 .claude/skills/lens-deep-insight/ 的分析框架
   对数据进行分析，生成 insights.md
   识别到 Claude Code 新功能 → 生成 alert

7. 保存报告到 reports/2026-02-17/ai-coding-tools/insights.md
   保存 alert 到 alerts/2026-02-17/ai-coding-tools.md

8. 记录分析到数据库

9. 更新 state.json 的 last_run

10. 收尾交互：
    报告中出现了 Claude Code 新功能（高信号），主动提问：
    "Claude Code 这次更新了 XX 能力，要不要我深入挖一下细节？
     或者持续盯着后续社区反馈？"
    用户回复后，根据反馈更新 memory/intent/vault。
    用户说"不用了"→ 正常结束。
```
