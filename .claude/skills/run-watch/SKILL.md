---
name: run-watch
description: 执行某个 Watch 的完整情报采集与分析流程。当用户要求运行、更新、检查某个 Watch，或者要求获取某个方向的最新情报时使用。
---

# run-watch 运行监控哨

## 完整工作流

### 1. 读取上下文
- 读取 `watches/{watch-name}/intent.md` — 监控意图
- 读取 `watches/{watch-name}/memory.md` — 历史反馈
- 读取 `watches/{watch-name}/state.json` — 运行状态
- 读取 `profile/identity.md` — 用户身份

### 2. 决定 Sensor 策略
根据 intent 语义自主选择合适的 Sensor（不要盲目全部调用）：
- 技术社区信号 → fetch-hacker-news, fetch-v2ex
- 开源项目趋势 → fetch-github-trending
- 定向关键词搜索 → fetch-tavily（需要自己生成查询词）
- 备选/补充网络搜索 → fetch-brave-search（独立索引，不依赖 Google）
- AI 语义搜索、深度内容发现 → fetch-exa（自然语言查询）
- 新产品发布、产品趋势 → fetch-product-hunt
- 用户需求、功能请求、痛点 → fetch-request-hunt
- 官方博客、changelog、长尾源 → fetch-rss（传入 feed URL）
- 社区讨论、用户反馈 → fetch-reddit
- 实时社交信号、产品动态 → fetch-x
- 新闻报道、行业动态 → fetch-news-api, fetch-gnews
- 学术论文、预印本、前沿研究 → fetch-arxiv
- 论文影响力、引用趋势、跨学科学术搜索 → fetch-openalex

### 3. 采集数据并存入数据库
依次调用选定的 Sensor skill，每个 sensor 的输出通过管道存入数据库：

```bash
# 方式一：sensor 输出管道存库（需要用 jq 或脚本注入 watch_name）
uv run python .claude/skills/fetch-hacker-news/scripts/fetch.py | uv run python .claude/skills/db-save-items/scripts/save.py

# 方式二（推荐）：sensor 输出保存到变量，合并 watch_name 后存库
# Claude 在调用时自行构造包含 watch_name 的 JSON
```

**关键**：存库时传入 `watch_name`，输出中的 `item_ids` 列表收集起来，后面记录分析时用。

Sensor 调用方式：
- Push 型（HN, GitHub, V2EX）：直接执行脚本
- Push+CLI 型（Product Hunt）：`uv run python .claude/skills/fetch-product-hunt/scripts/fetch.py --limit 20 --featured`
- Search 型（fetch-tavily, fetch-exa, fetch-brave-search, fetch-request-hunt, fetch-x, fetch-news-api, fetch-gnews, fetch-arxiv, fetch-openalex）：生成搜索词后通过 stdin 传入
- Feed 型（fetch-rss）：`echo '{"feeds": [...], "max_per_feed": 20}' | uv run python .claude/skills/fetch-rss/scripts/fetch.py`
- 混合型（fetch-reddit）：列表或搜索模式通过 stdin JSON 传入

### 4. 精简数据供分析

⚠️ **省 token 的关键步骤。不要把 sensor 原始 JSON 直接用于分析。**

将本次采集的原始数据通过预处理脚本精简：

```bash
echo '{"items": [...]}' | uv run python .claude/skills/db-save-items/scripts/summarize.py --limit 80
```

输出精简版：每条 item 只保留 `source`、`title`、`content`（截断至 150 字）、`url`。
这个精简版才是 LLM 分析的输入。原始数据已完整存入数据库，需要深挖时可以单独取。

### 5. 分析数据
- 选择合适的 Lens（参考 memory.md 中的偏好，默认 deep_insight）
- 读取对应 lens skill 的分析框架
- **用精简版数据作为分析输入**（不是原始 JSON，不是数据库查询结果）
- 对数据进行分析，生成报告
- 分析过程中自然识别高信号内容

### 6. 保存报告
使用 `save-report` skill 的指引保存报告和可能的 alert。

### 7. 记录分析
使用 `db-save-analysis` skill 记录本次运行，传入步骤 3 收集的 `item_ids`：

```bash
echo '{"watch_name": "...", "item_ids": [1,2,3,...], "report_path": "...", "item_count": N, "lens": "..."}' | uv run python .claude/skills/db-save-analysis/scripts/save.py
```

### 8. 更新状态
更新 `watches/{watch-name}/state.json` 的 `last_run` 为当前时间。

### 9. 推送通知
如果该 Watch 的 state.json 中配置了 `webhooks` 且 `webhooks.enabled: true`，调用 `webhook-notify` skill 推送。

**消息组装**：读取 `webhooks.targets` 中每个 enabled target 的 `content` 字段，据此组装消息。相同 `content` 的 target 可合并一次调用。

```bash
echo '{"watch": "{watch-name}", "message": "[Signex] {watch-name} 情报更新\n{根据 content 字段组装的内容}"}' | uv run python .claude/skills/webhook-notify/scripts/notify.py
```

⚠️ **只传 watch 名和消息文本。不要读取或传递 URL、secret 等凭据。**

如果 `webhooks` 不存在或 `enabled: false`，跳过此步。

### 10. 收尾交互
报告交付后，不要直接结束。根据本次运行的实际情况，选 1-2 个最相关的方向
与用户对话。目的是校准信号、发现深挖机会、沉淀洞察。

**选择哪些话题取决于本次数据，不要每次都问所有问题：**

- **信号校准**：报告中有明显的噪音或边缘内容时，问用户哪些发现有价值、
  哪些以后可以过滤。（例："这次出现了不少 XX 方向的内容，这个对你有用吗？
  还是以后可以过滤掉？"）
- **深挖意愿**：报告中出现高信号内容（alert 级别）时，主动提出可以深入。
  （例："XX 这个动态看起来比较重要，要不要我深入挖一下？"或"要不要我
  持续盯着这件事的后续？"）
- **洞察沉淀**：分析中出现跨领域的、有长期参考价值的观察时，建议存档。
  （例："这次发现的 XX 趋势可能不只和这个方向有关，要不要我记下来
  方便以后跨领域参考？"）
- **节奏感知**：数据量异常（太少或暴增）时，建议调整监控频率。
  （例："最近这个方向变化不大，要不要降低一下监控频率？"）
- **视角切换**：连续多次使用同一 lens 且数据特征发生变化时，建议换个角度。
  （例："这个话题最近变化很快，下次要不要换个角度梳理一下时间线？"）

**原则：**
- 问题要锚定到本次报告的具体内容上，不要泛泛地问"报告怎么样"
- 用户说"挺好"或不想聊也是有效信号，不要强行引导
- 不要暴露技术细节（不提文件名、配置项），只聊内容和方向

## 参考
详细决策树见 `references/workflow.md`。
