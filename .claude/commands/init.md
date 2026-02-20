---
name: init
description: 初始化 IntelStation 项目。创建用户数据目录和模板文件。幂等执行，不会覆盖已有内容。
---

# /init — 项目初始化

执行以下步骤初始化 IntelStation。**幂等原则：只创建缺失的目录和文件，绝不覆盖已有内容。**

## 1. 创建目录

确保以下 6 个目录存在（如已存在则跳过）：

- `watches/`
- `vault/`
- `profile/`
- `reports/`
- `alerts/`
- `data/`

## 2. 创建模板文件

逐个检查，**仅在文件不存在时创建**：

### watches/index.md

```markdown
# Watches

| Watch | Description | Status |
|-------|-------------|--------|
```

### vault/index.md

```markdown
# Vault

| Title | Summary | File | Tags |
|-------|---------|------|------|
```

### profile/identity.md

```markdown
# User Identity

(Edit this file to describe yourself. All Watches reference this profile.)

## Background
- Role: (e.g., independent developer, product manager, researcher)
- Domain: (e.g., AI/ML, web development, fintech)

## Preferences
- Report language: (e.g., Chinese, English)
- Focus: actionable insights over raw data
```

## 3. 初始化数据库

如果 `data/intel.db` 不存在，运行：

```bash
uv run python -c "from src.store.database import Database; db = Database(); db.init(); db.close()"
```

## 4. 检查 .env

如果 `.env` 不存在但 `.env.example` 存在，提醒用户（使用用户语言）：

> `.env` file not found. Copy `.env.example` to `.env` and fill in your API keys.

## 5. 完成

输出初始化结果摘要，列出创建了哪些目录和文件，跳过了哪些已存在的。

---

## Watch 文件模板参考

创建新 Watch 时（通过对话或 run-watch），按以下格式初始化：

### intent.md

```markdown
# {Watch 名称}

## Focus
（一句话描述监控方向）

## Key Interests
- （关注点 1）
- （关注点 2）

## Exclude
- （排除项，可选）

## Goal
（期望从这个 Watch 中获得什么）
```

### memory.md

初始为空文件。随用户反馈逐步积累。

### state.json

```json
{
  "check_interval": "1d",
  "status": "active",
  "last_run": null
}
```
