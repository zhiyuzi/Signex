中文 | [English](README.md)

<div align="center">

# Signex

**Signal + Nexus — 信号汇聚之处。**

个人情报 Agent，完全运行在 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 之上。

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)](https://www.python.org/)
[![Powered by Claude](https://img.shields.io/badge/Powered%20by-Claude-blueviolet.svg)](https://www.anthropic.com/)

</div>

---

## 它解决什么问题？

你关注 AI 编程工具赛道，每天要刷 Hacker News、GitHub Trending、Reddit、X、Product Hunt……十几个信息源，花一小时扫一遍，大部分是噪音，偶尔有一条关键信号差点漏掉。

Signex 替你干这件事。你用一句话描述关注方向，它自动从 15+ 数据源采集、去重、分析，给你一份带行动建议的报告。你只需要看结论、给反馈，它会越来越懂你要什么。

## 谁适合用？

- 独立开发者 — 盯产品机会、竞品动态、技术趋势
- 创业者 — 发现未被满足的需求、验证产品方向
- 技术负责人 — 跟踪行业方向、评估新工具和框架
- 产品经理 — 监控用户反馈、功能请求、市场信号
- 投资人 / 分析师 — 追踪赛道动态、发现早期信号
- 内容创作者 / 自媒体 — 捕捉热点话题、获取写作素材
- 研究者 — 持续跟踪特定领域的学术和产业进展

## Signex 是什么？

Signex 是你的 AI 情报分析师。你定义关注方向（Watch），它自主从多个数据源采集信息、用不同视角分析、生成可行动的报告。它会记住你的反馈，下次分析自动调整。

架构上，**Claude Code 就是运行时** — 没有独立的 app、server 或 CLI 包装。Agent 的行为完全由 `CLAUDE.md` 定义，能力以模块化 skill 的形式存放在 `.claude/skills/` 中。你直接和 Claude Code 对话来使用它。

## 核心概念

| 概念 | 作用 |
|------|------|
| **Watch** (监控哨) | 持续监控的意图方向。定义关注什么、什么信号重要。 |
| **Sensor** (探针) | 数据采集探针。每个 Sensor 对接一个数据源 — Hacker News、GitHub、Reddit、搜索 API、RSS 等。 |
| **Lens** (视角) | 分析视角。选择如何看待数据 — 深度洞察、快速速览、正反研判、时间线追踪。 |
| **Vault** (沉淀库) | 跨 Watch 的洞察存储。超越单个 Watch 的有价值发现沉淀于此。 |

## 架构

```mermaid
%%{init: {
  "theme": "base",
  "flowchart": { "curve": "basis", "nodeSpacing": 42, "rankSpacing": 60 },
  "themeVariables": {
    "background": "transparent",
    "mainBkg": "transparent",
    "fontFamily": "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial",
    "fontSize": "14px",
    "lineColor": "#94A3B8",
    "textColor": "#0F172A"
  }
}}%%

flowchart TB
  W["Watch<br/>intent.md + memory.md"]:::core --> S["Sensor 选择"]:::core

  subgraph Sensors["探针层 (可扩展)"]
    direction TB
    S --> S1["Hacker News"]:::sensor
    S --> S2["GitHub Trending"]:::sensor
    S --> S3["Tavily / Brave / Exa"]:::sensor
    S --> S4["Reddit / X / V2EX"]:::sensor
    S --> S5["Product Hunt / RSS / …"]:::sensor
    S --> S6["arXiv / OpenAlex"]:::sensor
    S --> S7["+ 自定义 Sensor"]:::sensorAlt
  end

  S1 & S2 & S3 & S4 & S5 & S6 & S7 --> DB[("SQLite")]:::store
  DB --> L{"Lens 视角"}:::decision

  subgraph Lenses["视角层 (可扩展)"]
    direction TB
    L --> L1["深度洞察"]:::lens
    L --> L2["快速速览"]:::lens
    L --> L3["正反研判"]:::lens
    L --> L4["时间线追踪"]:::lens
    L --> L5["+ 自定义 Lens"]:::lensAlt
  end

  L1 & L2 & L3 & L4 & L5 --> R["报告 & 警报"]:::out
  R --> U["你"]:::actor

  U -. "反馈 · 校准信号 · 调整方向" .-> W
  U -. "跨域洞察" .-> V["沉淀库"]:::vault

  classDef core      fill:#EEF2FF,stroke:#4F46E5,stroke-width:2px,color:#0F172A,rx:14,ry:14
  classDef sensor    fill:#ECFEFF,stroke:#06B6D4,stroke-width:1.6px,color:#0F172A,rx:12,ry:12
  classDef sensorAlt fill:#F0FDFA,stroke:#14B8A6,stroke-width:1.6px,color:#0F172A,stroke-dasharray:4 3,rx:12,ry:12
  classDef store     fill:#F1F5F9,stroke:#64748B,stroke-width:1.7px,color:#0F172A,rx:14,ry:14
  classDef decision  fill:#FFFFFF,stroke:#0EA5E9,stroke-width:2px,color:#0F172A,rx:18,ry:18
  classDef lens      fill:#FFF7ED,stroke:#F59E0B,stroke-width:1.6px,color:#0F172A,rx:12,ry:12
  classDef lensAlt   fill:#FFFBEB,stroke:#F59E0B,stroke-width:1.6px,color:#0F172A,stroke-dasharray:4 3,rx:12,ry:12
  classDef out       fill:#ECFDF5,stroke:#10B981,stroke-width:1.8px,color:#0F172A,rx:14,ry:14
  classDef vault     fill:#FDF4FF,stroke:#A855F7,stroke-width:1.6px,color:#0F172A,rx:14,ry:14
  classDef actor     fill:#FFF1F2,stroke:#FB7185,stroke-width:1.6px,color:#0F172A,rx:14,ry:14

  style Sensors fill:transparent,stroke:#CBD5E1,stroke-width:1.2px,rx:16,ry:16
  style Lenses  fill:transparent,stroke:#CBD5E1,stroke-width:1.2px,rx:16,ry:16

  linkStyle default stroke:#94A3B8,stroke-width:1.5px
```

## 快速开始

### 前置条件

- [Python 3.11+](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/)（Python 包管理器）
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)（CLI 工具）

### 安装

```bash
# 克隆仓库
git clone https://github.com/zhiyuzi/Signex.git
cd signex

# 安装依赖
uv sync

# 配置 API 密钥（至少配一个搜索类 API）
cp .env.example .env
# 编辑 .env 填入你的 API 密钥

# 在项目目录启动 Claude Code
claude
```

### 第一次使用

```
你：Hi
```

首次打招呼时 Signex 会自动初始化 — 创建用户画像、Watch 模板和沉淀库。然后给你一份态势简报。

```
你：帮我盯一下 AI 编程工具方向 — 新 IDE、agent 功能、社区反应。
```

Signex 根据你的意图创建 Watch，选择合适的 Sensor，准备就绪。

```
你：跑一下。
```

探针采集数据，存入 SQLite，视角分析，报告生成。

## Skills 清单

### Sensor（数据采集）

| Skill | 数据源 | 需要 API Key | 申请地址 |
|-------|--------|:---:|----------|
| `fetch-hacker-news` | Hacker News 首页 & 搜索 | — | |
| `fetch-github-trending` | GitHub Trending 仓库 | — | |
| `fetch-v2ex` | V2EX 中文技术社区 | — | |
| `fetch-reddit` | Reddit 帖子 & 搜索 | — | |
| `fetch-rss` | 任意 RSS/Atom 源 | — | |
| `fetch-tavily` | Tavily 网络搜索 | 是 | [tavily.com](https://app.tavily.com/sign-in) |
| `fetch-brave-search` | Brave Search | 是 | [brave.com](https://brave.com/search/api/) |
| `fetch-exa` | Exa AI 语义搜索 | 是 | [exa.ai](https://dashboard.exa.ai/login) |
| `fetch-product-hunt` | Product Hunt 新品发布 | 是 | [producthunt.com](https://www.producthunt.com/v2/oauth/applications) |
| `fetch-request-hunt` | RequestHunt 功能请求 | 是 | [requesthunt.com](https://www.requesthunt.com) |
| `fetch-news-api` | NewsAPI.org 新闻 | 是 | [newsapi.org](https://newsapi.org/register) |
| `fetch-gnews` | GNews 新闻 | 是 | [gnews.io](https://gnews.io) |
| `fetch-x` | X / Twitter 搜索 | 是 | [developer.x.com](https://developer.x.com/en/portal/dashboard) |
| `fetch-arxiv` | arXiv 预印本 | — | |
| `fetch-openalex` | OpenAlex 学术论文 | 是 | [openalex.org](https://openalex.org/settings/api) |

### Lens（分析视角）

| Skill | 用途 |
|-------|------|
| `lens-deep-insight` | 综合分析 — 关键发现、趋势、行动建议（默认） |
| `lens-flash-brief` | 3–5 条要点速览 |
| `lens-dual-take` | 正反论证研判 |
| `lens-timeline-trace` | 事件时间线梳理 |

### 数据库

| Skill | 用途 |
|-------|------|
| `db-save-items` | 存储采集数据（自动去重） |
| `db-query-items` | 按 Watch、来源、时间查询 |
| `db-save-analysis` | 记录分析运行 |
| `db-stats` | 运行历史统计 |
| `db-source-health` | 数据源健康监控 |

### 动作 & 编排

| Skill | 用途 |
|-------|------|
| `run-watch` | 执行完整 Watch 周期（采集 → 分析 → 报告） |
| `save-report` | 写入报告和警报 |
| `update-memory` | 将用户反馈整合到 Watch 记忆 |
| `extract-content` | 从 URL 提取文章全文 |
| `webhook-notify` | 报告生成后推送摘要到 IM 工具（飞书、Discord、企业微信等） |
| `webhook-setup` | 交互式 Webhook 配置向导 |
| `setup` | 项目初始化（目录、模板、数据库） |
| `skill-creator` | 创建新 Skill 的向导 |

## 项目结构

```
signex/
├── CLAUDE.md                  # Agent 行为定义（大脑）
├── .claude/skills/            # 所有 skill（sensor、lens、db、action）
├── profile/identity.md        # 用户画像
├── watches/                   # Watch 定义
│   ├── index.md               # Watch 索引
│   └── {watch-name}/
│       ├── intent.md          # 监控意图
│       ├── memory.md          # 反馈记忆
│       └── state.json         # 运行状态
├── vault/                     # 跨 Watch 洞察沉淀
│   ├── index.md               # 沉淀库索引
│   └── *.md                   # 独立洞察笔记
├── reports/{date}/{watch}/    # 分析报告
├── alerts/{date}/             # 高信号警报
├── knowledge/                 # Skill 知识库（参考文档）
├── data/signex.db             # SQLite 数据库
├── src/                       # Python 脚本（仅 HTTP 调用 + SQLite 操作）
└── .env                       # API 密钥（不提交）
```

## 许可证

Copyright (c) 2026 Li Ze

本项目采用 [GNU Affero 通用公共许可证 v3.0](LICENSE) 授权。

你可以自由使用、修改和分发本软件。如果你将修改版本作为网络服务运行，必须向用户提供源代码。
