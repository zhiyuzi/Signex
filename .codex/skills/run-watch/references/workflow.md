# run-watch 决策树

## Sensor 选择决策

根据 Watch intent 中的关键词和方向选择 Sensor：

| Intent 关键特征 | 推荐 Sensor |
|-----------------|-------------|
| 英语技术社区、开发者工具、创业 | fetch-hacker-news |
| 开源项目、GitHub、技术工具 | fetch-github-trending |
| 中文社区、国内技术、产品反馈 | fetch-v2ex |
| 需要定向搜索特定话题 | fetch-tavily |
| 新产品发布、产品趋势 | fetch-product-hunt |
| 用户需求、功能请求、痛点挖掘 | fetch-request-hunt |
| 官方博客、changelog、长尾源 | fetch-rss |
| 社区讨论、用户反馈、痛点 | fetch-reddit |
| AI 语义搜索、深度内容发现 | fetch-exa |
| 实时社交信号、产品发布动态 | fetch-x |
| 新闻报道、行业动态 | fetch-news-api, fetch-gnews |
| 备选/补充网络搜索（独立索引） | fetch-brave-search |
| 学术论文、预印本、前沿研究 | fetch-arxiv |
| 论文影响力、引用趋势、跨学科学术搜索 | fetch-openalex |

**原则**：宁可少调不调多。每个 Sensor 都有成本（时间、API 配额）。
如果 intent 明确聚焦某个方向，只调相关的 1-2 个 Sensor。

## 搜索词生成（Search 型 Sensor）

当使用 Search 型 sensor 时，需要根据 intent 生成搜索词：

1. 提取 intent 中的核心关注点（3-5 个）
2. 为每个关注点生成 1-2 个搜索查询
3. **每个查询必须包含年月**（如 "2026-02"）
4. 参考 memory.md 中的排除项，避免搜索已排除的内容
5. 混合中英文查询以获得更好的覆盖

**Sensor 特性差异：**
- **fetch-tavily**：关键词+时间搜索，适合精确话题追踪
- **fetch-exa**：语义相似度搜索，适合自然语言描述（如 "tools that help developers write code faster"），不需要精确关键词
- **fetch-x**：社交信号搜索，查询词应简短（Twitter 搜索语法），适合追踪产品名、事件。按量计费（~$0.005/条），建议 max_results 10，配合 min_likes 过滤噪音
- **fetch-brave-search**：备选网络搜索（独立索引，不依赖 Google），$5/1000 requests，建议 count 10，1-2 个 query。仅在 Tavily 不可用或需要交叉验证时使用
- **fetch-news-api / fetch-gnews**：新闻搜索，适合行业动态、公司新闻
- **fetch-arxiv**：学术预印本搜索，关键词+分类过滤（如 cs.AI, cs.CL），适合追踪特定领域最新论文提交。查询词应偏学术（如 "large language model agent" 而非 "AI coding tools"）
- **fetch-openalex**：学术论文搜索+引用排序，覆盖 2.5 亿+ 作品，适合发现高引用论文和跨学科关联。支持年份、类型过滤，返回引用数和 FWCI 影响力指标

示例（ai-coding-tools watch）：
```json
// fetch-tavily（关键词精确搜索）
{"queries": ["AI native IDE 2026-02 new release", "Cursor AI IDE update February 2026"], "days": 7}

// fetch-exa（语义搜索，自然语言描述）
{"queries": ["AI-powered code editors and IDE tools launched recently", "developer tools using LLM for code generation"], "num_results": 10, "days": 7}

// fetch-x（社交信号，简短查询，min_likes 过滤低质量）
{"queries": ["Cursor IDE", "Claude Code"], "max_results": 10, "min_likes": 5}

// fetch-brave-search（备选搜索，仅在需要交叉验证或 Tavily 不可用时）
{"queries": ["AI coding tools 2026"], "count": 10}

// fetch-news-api / fetch-gnews（新闻搜索）
{"queries": ["AI developer tools", "AI coding assistant"], "days": 7}

// fetch-arxiv（学术预印本，关键词+分类过滤）
{"queries": ["large language model agent", "code generation LLM"], "categories": ["cs.AI", "cs.CL", "cs.SE"], "max_results": 20}

// fetch-openalex（学术论文搜索，引用排序）
{"queries": ["LLM agent framework", "AI code generation"], "per_page": 20, "publication_year": "2025-2026"}
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
   $ echo '{"queries": ["AI native IDE tools", ...], "num_results": 10, "days": 7}' | uv run python .claude/skills/fetch-exa/scripts/search.py
   $ uv run python .claude/skills/fetch-product-hunt/scripts/fetch.py --limit 20 --featured
   $ echo '{"queries": ["AI IDE feature requests"], "limit": 20}' | uv run python .claude/skills/fetch-request-hunt/scripts/search.py
   $ echo '{"feeds": ["https://blog.cursor.com/rss.xml"], "max_per_feed": 20}' | uv run python .claude/skills/fetch-rss/scripts/fetch.py
   $ echo '{"subreddits": ["SaaS", "startups"], "sort": "hot", "limit": 25}' | uv run python .claude/skills/fetch-reddit/scripts/fetch.py
   $ echo '{"queries": ["Cursor IDE", "Claude Code"], "max_results": 10, "min_likes": 5}' | uv run python .claude/skills/fetch-x/scripts/search.py
   $ echo '{"queries": ["AI developer tools"], "days": 7}' | uv run python .claude/skills/fetch-news-api/scripts/search.py
   $ echo '{"queries": ["AI coding tools"], "max_results": 10}' | uv run python .claude/skills/fetch-gnews/scripts/search.py
   $ echo '{"queries": ["large language model code generation"], "categories": ["cs.AI", "cs.SE"], "max_results": 20}' | uv run python .claude/skills/fetch-arxiv/scripts/search.py
   $ echo '{"queries": ["LLM code generation"], "per_page": 20, "publication_year": "2025-2026"}' | uv run python .claude/skills/fetch-openalex/scripts/search.py

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
