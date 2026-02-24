---
name: webhook-notify
description: Watch 运行完成后推送通知到 Webhook。读取 state.json 中的 webhooks 配置，检查双层 enabled 开关，自动发送到飞书等平台。
---

# webhook-notify 通知推送

## 何时使用

run-watch 流程第 10 步，报告保存后调用。

## 调用方式

```bash
echo '{"watch": "ai-coding-tools", "message": "[Signex] ai-coding-tools 情报更新\n发现 3 个关键信号..."}' | uv run python .claude/skills/webhook-notify/scripts/notify.py
```

**参数：**
- `watch`：Watch 名称（对应 `watches/{watch}/` 目录）
- `message`：推送的消息文本（根据 target 的 `content` 字段组装）

## 开关逻辑

1. `webhooks` 不存在 → 不推送
2. `webhooks.enabled: false` → 不推送（全局关）
3. `webhooks.enabled: true` → 检查每个 target
4. target `enabled: false` → 跳过
5. target `enabled: true` → 推送

## 消息组装

每个 target 有 `content` 字段指定推送内容方向。Claude 在调用前根据 `content` 组装消息：

- `"summary"`（默认）— 报告摘要
- `"brief"` — 一句话概要
- `"key_findings"` — 关键发现要点
- 自定义描述 — Claude 自行判断

如果多个 target 的 `content` 不同，需分别组装消息、分别调用。

## 输出

```json
{
  "success": true,
  "results": [
    {"url": "https://...", "status": "ok"}
  ],
  "error": ""
}
```
