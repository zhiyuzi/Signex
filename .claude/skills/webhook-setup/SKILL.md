---
name: webhook-setup
description: 交互式 Webhook 配置向导。引导用户选择平台、填写 URL/secret、设置推送内容偏好，将配置写入 state.json。
---

# webhook-setup 配置向导

## 何时使用

用户想配置 Webhook 推送，或不知道怎么配置时使用。

## 流程

1. 读取 `knowledge/webhook-setup-guide.md` 获取平台配置知识
2. **确认目标 Watch**：
   - 读取 `watches/index.md` 获取所有 active Watch 列表
   - 如果用户已指定 Watch，直接使用
   - 如果只有一个 active Watch，默认使用它，无需询问
   - 如果有多个 active Watch 且用户未指定，**必须列出让用户选择**，不得自行推断
3. **去重检查**：
   - 读取目标 Watch 的 `state.json`，检查 `webhooks.targets` 中是否已有相同 `platform + url` 的 target
   - 如果已存在完全相同的配置，告知用户"这个 Webhook 已经配置过了"，询问是否要修改内容偏好或其他设置
   - 如果同平台但不同 URL，正常追加
4. 引导用户完成配置：
   - 选平台（飞书、Discord、企业微信已支持，其他待扩展）
   - 填 Webhook URL（引导用户在 IM 工具中创建机器人获取）
   - 填 secret（可选，飞书签名校验模式需要）
   - 选推送内容偏好（content 字段：summary / brief / key_findings / 自定义）
   - 确认 enabled 状态
5. 将配置写入 `watches/{watch}/state.json` 的 `webhooks` 字段

## 写入规则

**首次配置**（`webhooks` 不存在）：

```json
"webhooks": {
  "enabled": true,
  "targets": [
    {
      "platform": "feishu",
      "url": "...",
      "secret": "",
      "enabled": true,
      "content": "summary"
    }
  ]
}
```

**已有配置且全局 `enabled: true`**：直接追加 target（`enabled: true`）。

**已有配置但全局 `enabled: false`**：追加 target 后，提醒用户全局开关是关的，问是否开启。

## 注意

- 不要在对话中展示用户填写的 URL 和 secret（避免上下文泄露）
- 写入 state.json 时保留已有字段（check_interval、status、last_run 等）
- 如果用户要修改已有 target，按 URL 匹配定位
