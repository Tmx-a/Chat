# 修复消息发送重复和刷新后消失问题计划

## 问题分析

### 问题1：发送一条消息显示两条
消息发送流程存在问题：
1. 用户发送消息时，创建临时消息（`id: tempId`, `client_message_id: clientMessageId`）
2. WebSocket 收到服务器响应后调用 `updateMessage`，将临时消息替换为服务器返回的消息
3. 但是 `updateMessage` 替换消息时，没有保留 `client_message_id` 字段
4. 导致后续如果有其他地方调用 `addMessage`，会认为这是新消息而添加

**当前 `updateMessage` 函数：**
```javascript
function updateMessage(conversationId, clientMessageId, newMessage) {
  if (!messages.value[conversationId]) return;
  const index = messages.value[conversationId].findIndex(
    (m) => m.client_message_id === clientMessageId,
  );
  if (index !== -1) {
    messages.value[conversationId][index] = {
      ...newMessage,
      _sending: false,
      _error: false,
    };
  }
}
```

**问题：** 替换消息时没有保留 `client_message_id`，导致后续可能重复添加。

### 问题2：刷新网页后消息消失
可能的原因：
1. 后端消息查询逻辑有问题
2. 前端消息加载逻辑有问题
3. 消息没有正确保存到数据库

## 修复方案

### 步骤1：修复 `updateMessage` 函数
保留 `client_message_id` 字段，防止重复添加：

```javascript
function updateMessage(conversationId, clientMessageId, newMessage) {
  if (!messages.value[conversationId]) return;
  const index = messages.value[conversationId].findIndex(
    (m) => m.client_message_id === clientMessageId,
  );
  if (index !== -1) {
    messages.value[conversationId][index] = {
      ...newMessage,
      client_message_id: clientMessageId,  // 保留 client_message_id
      _sending: false,
      _error: false,
    };
  }
}
```

### 步骤2：增强 `addMessage` 函数
检查 `client_message_id` 是否已存在，防止重复添加：

```javascript
function addMessage(conversationId, message) {
  if (!messages.value[conversationId]) {
    messages.value[conversationId] = [];
  }
  const exists = messages.value[conversationId].some(
    (m) => m.id === message.id || m.client_message_id === message.client_message_id,
  );
  if (!exists) {
    messages.value[conversationId].push(message);
  }
}
```

### 步骤3：确保消息正确保存
检查后端消息保存逻辑，确保消息被正确保存到数据库。

## 涉及文件
1. `frontend/src/stores/chat.js` - 修改 `updateMessage` 和 `addMessage` 函数
