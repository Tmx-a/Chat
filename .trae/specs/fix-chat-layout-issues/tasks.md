# Tasks

## 第一阶段：修复消息布局问题

- [x] Task 1: 修复消息间距问题
  - [x] 1.1 增加 `.message-wrapper` 的 margin-bottom 从 var(--spacing-md) 改为 var(--spacing-lg)
  - [x] 1.2 调整 `.message-list` 的 gap 从 var(--spacing-lg) 改为 var(--spacing-xl)
  - [x] 1.3 调整连续消息 `.message-wrapper.consecutive` 的 margin-top

- [x] Task 2: 修复自己消息居中问题
  - [x] 2.1 修改 `.message-wrapper.self` 的 max-width 为固定值 500px
  - [x] 2.2 确保 `align-self: flex-end` 正确生效
  - [x] 2.3 移除 `min(70%, var(--chat-max-width))` 的计算方式

- [x] Task 3: 修复已读/未读提示被遮挡问题
  - [x] 3.1 调整 `.message-status` 的位置，确保在消息气泡下方
  - [x] 3.2 增加 `.message-status` 的 margin-top
  - [x] 3.3 确保消息气泡不会遮挡状态指示

## 第二阶段：修复输入框问题

- [x] Task 4: 修复输入框文字位置问题
  - [x] 4.1 调整 `.input-wrapper` 的 padding，移除上方空白
  - [x] 4.2 调整 `.message-input :deep(.el-textarea__inner)` 的 line-height
  - [x] 4.3 确保 textarea 内容垂直居中

## 第三阶段：修复消息发送重复问题

- [x] Task 5: 修复消息发送重复和转圈问题
  - [x] 5.1 检查 Chat.vue 中 sendMessage 函数的逻辑
  - [x] 5.2 确保临时消息被正确替换而非重复添加
  - [x] 5.3 修复 WebSocket 消息回调处理逻辑
  - [x] 5.4 确保 `_sending` 状态在收到服务器响应后正确更新

# Task Dependencies
- Task 1-3 可并行执行（布局问题修复）
- Task 4 可独立执行
- Task 5 需要仔细检查消息发送和接收逻辑
