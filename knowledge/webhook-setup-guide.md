# Webhook 配置知识库

本文件供 webhook-setup 技能读取，用于引导用户完成 Webhook 配置。

## 支持的平台

| 平台 | platform 标识 | 状态 |
|------|--------------|------|
| 飞书 | `feishu` | ✅ 已支持 |
| 钉钉 | `dingtalk` | 待扩展 |
| 企业微信 | `wecom` | 待扩展 |
| Slack | `slack` | 待扩展 |
| Discord | `discord` | 待扩展 |
| Telegram | `telegram` | 待扩展 |
| Microsoft Teams | `teams` | 待扩展 |

## 飞书配置步骤

1. 打开飞书群 → 群设置 → 群机器人 → 添加机器人
2. 选择"自定义机器人"
3. 设置机器人名称（如 "Signex 情报推送"）
4. 选择安全设置（三种模式任选其一）
5. 复制 Webhook URL

### 安全模式

**签名校验（推荐）**：飞书给一个签名密钥（secret），Signex 发消息时自动签名。需要在 state.json 中填 `secret` 字段。

**自定义关键词**：消息中必须包含指定关键词。建议设为 "Signex"，推送消息默认含 `[Signex]` 前缀。`secret` 留空。

**IP 白名单**：只允许指定 IP 调用。`secret` 留空。

## state.json 配置结构

```json
{
  "webhooks": {
    "enabled": true,
    "targets": [
      {
        "platform": "feishu",
        "url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxxx",
        "secret": "",
        "enabled": true,
        "content": "summary"
      }
    ]
  }
}
```

### content 选项

- `"summary"` — 报告摘要（默认）
- `"brief"` — 一句话概要
- `"key_findings"` — 关键发现要点
- 自定义描述 — 如 `"只推送高信号发现"`

## 常见问题

- 不配置 webhooks 不影响现有功能
- 推送失败不影响报告生成
- 全局 `enabled: false` 时所有 target 都不推送
