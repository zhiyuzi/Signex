---
name: update-memory
description: 更新 Watch 的 memory.md 文件。当用户对报告或分析给出反馈时使用，将新反馈整合到现有记忆中。
---

# update-memory 更新记忆

## 使用场景
用户对报告给出反馈、偏好或修正时，更新对应 Watch 的 memory.md。

## 操作步骤
1. 读取 `watches/{watch-name}/memory.md`
2. 理解用户的反馈内容
3. 将新反馈按主题整合到 memory.md 中（不是简单追加，是重组）
4. 使用 Edit 工具更新文件

## 整合原则
- 按主题分组（关注方向、排除项、lens 偏好、格式偏好等）
- 新反馈覆盖旧的矛盾信息
- 保持简洁，每个主题 1-3 行
- 不要保留原始对话记录，只保留压缩后的偏好

## 示例
用户说："以后 AI coding tools 的分析用 flash_brief 就好"

更新后的 memory.md:
```
### 关注方向
- 重点聚焦标杆产品Claude Code的相关新功能

### 排除项
- 暂不关注Windsurf相关内容

### 分析偏好
- 默认使用 flash_brief lens
```
