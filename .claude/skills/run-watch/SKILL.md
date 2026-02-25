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

⚠️ **必须先读取 `references/workflow.md`**，其中包含：Sensor 选择决策表、搜索词生成规则、每个 Sensor 的完整调用示例。

根据 intent 语义自主选择合适的 Sensor（不要盲目全部调用）。

**防幻觉提醒 — 脚本名和参数格式：**
- Push 型脚本名为 `fetch.py`：fetch-hacker-news, fetch-github-trending, fetch-v2ex, fetch-product-hunt
- Search 型脚本名为 `search.py`：fetch-tavily, fetch-brave-search, fetch-exa, fetch-request-hunt, fetch-x, fetch-news-api, fetch-gnews, fetch-arxiv, fetch-openalex
- 混合型脚本名为 `fetch.py` 但需要 stdin：fetch-reddit, fetch-rss
- **所有 Search 型 sensor 的查询参数字段名为 `queries`（复数，数组），不是 `query`（单数）**
- 不确定参数格式时，**必须读取对应 sensor 的 SKILL.md** 确认

### 3. 采集数据并存入数据库
依次调用选定的 Sensor skill，每个 sensor 的输出通过管道存入数据库：

```bash
# Push 型：直接管道，中间注入 watch_name
uv run python .claude/skills/fetch-hacker-news/scripts/fetch.py | uv run python -c "
import json, sys; data = json.load(sys.stdin); data['watch_name'] = '{watch-name}'; json.dump(data, sys.stdout)
" | uv run python .claude/skills/db-save-items/scripts/save.py

# Search 型：stdin 传参，输出同样管道存库
echo '{"queries": [...], "days": 7}' | uv run python .claude/skills/fetch-tavily/scripts/search.py | uv run python -c "
import json, sys; data = json.load(sys.stdin); data['watch_name'] = '{watch-name}'; json.dump(data, sys.stdout)
" | uv run python .claude/skills/db-save-items/scripts/save.py
```

save.py 的输出包含两个关键字段：
- `item_ids`：新插入的 ID 列表，收集起来供步骤 7 记录分析用
- `summary`：所有 items 的精简版（仅 source/title/content 前 150 字/url），**这就是步骤 4 分析用的数据**

完整的 Sensor 调用示例见 `references/workflow.md`。

### 4. 分析数据

⚠️ **只用 save.py 输出的 `summary` 字段做分析，不要回头看 sensor 原始输出。**

- 选择合适的 Lens（参考 memory.md 中的偏好，默认 deep_insight）
- 读取对应 lens skill 的分析框架
- **分析输入 = 步骤 3 中各 save.py 返回的 `summary` 数组合并**
- 对数据进行分析，生成报告
- 分析过程中自然识别高信号内容

如果 summary 中某条 item 信号很强但 150 字不够判断，可用 `db-query-items` 查完整记录，或用 `extract-content` 抓取原文。

**不要创建临时文件或编写额外脚本。不要用 sensor 原始 JSON 做分析。**

### 5. 保存报告
使用 `save-report` skill 的指引保存报告和可能的 alert。

### 6. 记录分析
使用 `db-save-analysis` skill 记录本次运行，传入步骤 3 收集的 `item_ids`：

```bash
echo '{"watch_name": "...", "item_ids": [1,2,3,...], "report_path": "...", "item_count": N, "lens": "..."}' | uv run python .claude/skills/db-save-analysis/scripts/save.py
```

### 7. 更新状态
更新 `watches/{watch-name}/state.json` 的 `last_run` 为当前时间。

### 8. 推送通知
如果该 Watch 的 state.json 中配置了 `webhooks` 且 `webhooks.enabled: true`，调用 `webhook-notify` skill 推送。

**消息组装**：读取 `webhooks.targets` 中每个 enabled target 的 `content` 字段，据此组装消息。相同 `content` 的 target 可合并一次调用。

```bash
echo '{"watch": "{watch-name}", "message": "[Signex] {watch-name} 情报更新\n{根据 content 字段组装的内容}"}' | uv run python .claude/skills/webhook-notify/scripts/notify.py
```

⚠️ **只传 watch 名和消息文本。不要读取或传递 URL、secret 等凭据。**

如果 `webhooks` 不存在或 `enabled: false`，跳过此步。

### 9. 收尾交互
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
