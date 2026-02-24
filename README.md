[中文](README.zh-CN.md) | English

<div align="center">

# Signex

**Signal + Nexus — where signals converge.**

A personal intelligence agent that runs entirely inside [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)](https://www.python.org/)
[![Powered by Claude](https://img.shields.io/badge/Powered%20by-Claude-blueviolet.svg)](https://www.anthropic.com/)

</div>

---

## The Problem

You're tracking the AI coding tools space. Every day you check Hacker News, GitHub Trending, Reddit, X, Product Hunt… a dozen sources, an hour of scanning, mostly noise, and you still almost miss that one critical signal.

Signex does this for you. Describe what you care about in one sentence, and it automatically collects from 15+ data sources, deduplicates, analyzes, and delivers a report with actionable insights. You read the conclusions, give feedback, and it learns what matters to you.

## Who Is This For?

- Indie developers — tracking product opportunities, competitors, tech trends
- Startup founders — discovering unmet needs, validating product direction
- Tech leads — following industry direction, evaluating new tools and frameworks
- Product managers — monitoring user feedback, feature requests, market signals
- Investors / analysts — tracking market dynamics, spotting early signals
- Content creators — catching trending topics, sourcing writing material
- Researchers — continuously following developments in a specific domain

## What is Signex?

Signex is your AI intelligence analyst. You define what you care about (a "Watch"), and it autonomously collects data from multiple sources, analyzes it through different lenses, and delivers actionable reports. It remembers your feedback and adjusts future analysis accordingly.

Architecturally, **Claude Code IS the runtime.** There is no standalone app, server, or CLI wrapper. The agent's behavior is defined entirely in `CLAUDE.md`, and its capabilities are modular skills in `.claude/skills/`. You interact with it by talking to Claude Code.

## Core Concepts

| Concept | What it does |
|---------|-------------|
| **Watch** | A continuous monitoring intent. Defines what direction to watch and what signals matter. |
| **Sensor** | Data collection probes. Each sensor fetches from a specific source — Hacker News, GitHub, Reddit, search APIs, RSS, etc. |
| **Lens** | Analysis perspectives. Choose how to look at the data — deep insight, quick brief, pro/con evaluation, or timeline trace. |
| **Vault** | Cross-watch insight storage. Valuable findings that transcend individual watches get deposited here. |

## Architecture

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
  W["Watch<br/>intent.md + memory.md"]:::core --> S["Sensor Selection"]:::core

  subgraph Sensors["Sensors (extensible)"]
    direction TB
    S --> S1["Hacker News"]:::sensor
    S --> S2["GitHub Trending"]:::sensor
    S --> S3["Tavily / Brave / Exa"]:::sensor
    S --> S4["Reddit / X / V2EX"]:::sensor
    S --> S5["Product Hunt / RSS / …"]:::sensor
    S --> S6["arXiv / OpenAlex"]:::sensor
    S --> S7["+ Your Own Sensor"]:::sensorAlt
  end

  S1 & S2 & S3 & S4 & S5 & S6 & S7 --> DB[("SQLite")]:::store
  DB --> L{"Lens"}:::decision

  subgraph Lenses["Lenses (extensible)"]
    direction TB
    L --> L1["Deep Insight"]:::lens
    L --> L2["Flash Brief"]:::lens
    L --> L3["Dual Take"]:::lens
    L --> L4["Timeline Trace"]:::lens
    L --> L5["+ Your Own Lens"]:::lensAlt
  end

  L1 & L2 & L3 & L4 & L5 --> R["Reports & Alerts"]:::out
  R --> U["You"]:::actor

  U -. "feedback · calibrate signals · adjust scope" .-> W
  U -. "cross-watch insights" .-> V["Vault"]:::vault

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

## Quick Start

### Prerequisites

- [Python 3.11+](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (the CLI)

### Setup

```bash
# Clone the repo
git clone https://github.com/zhiyuzi/Signex.git
cd signex

# Install dependencies
uv sync

# Configure API keys (at minimum, set one search API key)
cp .env.example .env
# Edit .env with your API keys

# Start Claude Code in the project directory
claude
```

### First Run

```
You:  Hi
```

Signex initializes automatically on first greeting — creates your profile, watch templates, and vault. Then it gives you a situational briefing.

```
You:  Help me watch AI coding tools — new IDEs, agent features, community reactions.
```

Signex creates a new Watch with your intent, picks relevant sensors, and is ready to run.

```
You:  Run it.
```

Sensors fire, data flows into SQLite, the lens analyzes, and you get a report.

## Skills

### Sensors (data collection)

| Skill | Source | API Key | Get Key |
|-------|--------|:---:|---------|
| `fetch-hacker-news` | Hacker News front page & search | — | |
| `fetch-github-trending` | GitHub Trending repos | — | |
| `fetch-v2ex` | V2EX (Chinese tech community) | — | |
| `fetch-reddit` | Reddit posts & search | — | |
| `fetch-rss` | Any RSS/Atom feed | — | |
| `fetch-tavily` | Tavily web search | Yes | [tavily.com](https://app.tavily.com/sign-in) |
| `fetch-brave-search` | Brave Search | Yes | [brave.com](https://brave.com/search/api/) |
| `fetch-exa` | Exa AI semantic search | Yes | [exa.ai](https://dashboard.exa.ai/login) |
| `fetch-product-hunt` | Product Hunt launches | Yes | [producthunt.com](https://www.producthunt.com/v2/oauth/applications) |
| `fetch-request-hunt` | RequestHunt feature requests | Yes | [requesthunt.com](https://www.requesthunt.com) |
| `fetch-news-api` | NewsAPI.org | Yes | [newsapi.org](https://newsapi.org/register) |
| `fetch-gnews` | GNews | Yes | [gnews.io](https://gnews.io) |
| `fetch-x` | X / Twitter search | Yes | [developer.x.com](https://developer.x.com/en/portal/dashboard) |
| `fetch-arxiv` | arXiv preprints | — | |
| `fetch-openalex` | OpenAlex academic papers | Yes | [openalex.org](https://openalex.org/settings/api) |

### Lenses (analysis)

| Skill | Purpose |
|-------|---------|
| `lens-deep-insight` | Comprehensive analysis — key findings, trends, action items (default) |
| `lens-flash-brief` | 3–5 bullet quick summary |
| `lens-dual-take` | Pro/con evaluation of a topic |
| `lens-timeline-trace` | Event timeline reconstruction |

### Database

| Skill | Purpose |
|-------|---------|
| `db-save-items` | Store sensor data (auto-dedup) |
| `db-query-items` | Query items by watch, source, time |
| `db-save-analysis` | Record analysis runs |
| `db-stats` | Run history & statistics |
| `db-source-health` | Data source health monitoring |

### Actions & Orchestration

| Skill | Purpose |
|-------|---------|
| `run-watch` | Execute full watch cycle (collect → analyze → report) |
| `save-report` | Write reports and alerts to disk |
| `update-memory` | Integrate user feedback into watch memory |
| `extract-content` | Extract full article text from URLs |
| `webhook-notify` | Push report summary to IM tools (Feishu, etc.) |
| `webhook-setup` | Interactive webhook configuration wizard |
| `setup` | Project initialization (directories, templates, database) |
| `skill-creator` | Guide for creating new skills |

## Project Structure

```
signex/
├── CLAUDE.md                  # Agent behavior definition (the brain)
├── .claude/skills/            # All skills (sensor, lens, db, action)
├── profile/identity.md        # User identity & preferences
├── watches/                   # Watch definitions
│   ├── index.md               # Watch registry
│   └── {watch-name}/
│       ├── intent.md          # What to monitor
│       ├── memory.md          # Accumulated feedback
│       └── state.json         # Run state
├── vault/                     # Cross-watch insights
│   ├── index.md               # Vault index
│   └── *.md                   # Individual insight notes
├── reports/{date}/{watch}/    # Analysis output
├── alerts/{date}/             # High-signal alerts
├── knowledge/                 # Skill knowledge base (reference docs)
├── data/signex.db             # SQLite database
├── src/                       # Python scripts (HTTP + SQLite only)
└── .env                       # API keys (not committed)
```

## License

Copyright (c) 2026 Li Ze

This project is licensed under the [GNU Affero General Public License v3.0](LICENSE).

You are free to use, modify, and distribute this software under the terms of the AGPL-3.0. If you run a modified version as a network service, you must make the source code available to its users.
