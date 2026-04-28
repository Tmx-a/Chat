# Tasks

- [x] Task 1: 后端WebSocket消息广播优化
  - [x] 1.1 修改consumers.py：新消息发送到用户个人频道
  - [x] 1.2 添加新消息类型：new_message_notification
  - [x] 1.3 消息包含会话信息和发送者信息

- [x] Task 2: 后端未读消息计数
  - [x] 2.1 ConversationSerializer添加unread_count字段
  - [x] 2.2 计算当前用户在每个会话的未读消息数
  - [x] 2.3 标记已读时清除未读计数

- [x] Task 3: 前端WebSocket消息处理
  - [x] 3.1 添加new_message_notification消息处理
  - [x] 3.2 更新会话列表中的最新消息
  - [x] 3.3 更新未读消息计数

- [x] Task 4: 前端会话列表UI更新
  - [x] 4.1 会话项显示未读消息角标
  - [x] 4.2 收到新消息时会话移到顶部
  - [x] 4.3 打开会话时清除未读计数

- [x] Task 5: 前端Store状态管理
  - [x] 5.1 添加unreadCounts状态
  - [x] 5.2 添加updateConversation方法
  - [x] 5.3 添加incrementUnread方法

# Task Dependencies
- Task 3 依赖 Task 1（WebSocket消息格式）
- Task 4 依赖 Task 2（后端返回未读计数）
- Task 5 依赖 Task 2（后端返回未读计数）