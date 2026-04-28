# 消息实时推送与未读消息修复 Spec

## Why
当前A给B发消息时，如果B没有打开与A的对话框，B不会实时收到消息更新，也不会显示未读消息数量，导致用户体验不佳。

## What Changes
- WebSocket消息广播机制优化：向用户的所有会话推送新消息
- 未读消息计数：后端返回每个会话的未读消息数量
- 前端会话列表实时更新：显示未读消息数量角标
- 新消息到达时会话列表自动更新

## Impact
- Affected specs: 消息系统、会话系统
- Affected code:
  - 后端: chat/consumers.py, chat/views.py, chat/serializers.py
  - 前端: Chat.vue, stores/chat.js, utils/websocket.js

---

## ADDED Requirements

### Requirement: 消息实时推送
系统 SHALL 向用户推送所有相关会话的新消息，而不仅仅是当前打开的会话。

#### Scenario: 接收新消息
- **WHEN** 用户A向用户B发送消息
- **AND** 用户B未打开与A的会话
- **THEN** 用户B的会话列表实时更新
- **AND** 用户B看到新消息预览
- **AND** 用户B看到未读消息数量

### Requirement: 未读消息计数
系统 SHALL 为每个会话显示未读消息数量。

#### Scenario: 显示未读数量
- **WHEN** 用户有未读消息
- **THEN** 会话列表显示未读消息数量角标
- **AND** 打开会话后未读数量清零

### Requirement: 会话列表实时更新
系统 SHALL 在收到新消息时实时更新会话列表。

#### Scenario: 会话列表更新
- **WHEN** 用户收到新消息
- **THEN** 会话列表中对应会话移到顶部
- **AND** 显示最新消息预览
- **AND** 显示未读数量（如果会话未打开）
