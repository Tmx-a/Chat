# 修复聊天消息布局和重复问题计划

## 问题分析

### 问题1：自己的消息在中间，应该在最右边
当前 `.message-wrapper.self` 有 `align-self: flex-end`，但消息仍然显示在中间。原因是：
- `.message-wrapper` 设置了 `max-width: 500px`
- 但没有设置 `margin-left: auto` 来确保靠右对齐
- `align-self: flex-end` 在某些情况下可能不够

### 问题2：发送一条消息显示两条
消息发送流程存在问题：
1. `sendMessage` 函数创建临时消息（带 `client_message_id` 和 `tempId`）
2. WebSocket 收到服务器响应后调用 `updateMessage`，通过 `client_message_id` 查找并替换临时消息
3. 同时 Promise 解析后，`sendMessage` 函数又尝试通过 `tempId` 查找并替换消息
4. 由于 `updateMessage` 已经替换了消息（ID 已变），`sendMessage` 中的 `tempId` 查找失败
5. 但 `updateMessage` 中有 `else` 分支，当找不到消息时会 `addMessage`，导致重复

## 修复步骤

### 步骤1：修复消息位置问题
修改 `.message-wrapper.self` 样式，添加 `margin-left: auto` 确保消息靠右：
```css
.message-wrapper.self {
  flex-direction: row-reverse;
  align-self: flex-end;
  margin-left: auto;
}
```

### 步骤2：修复消息重复问题
修改 `sendMessage` 函数，移除手动替换逻辑，完全依赖 WebSocket 的 `updateMessage`：
```javascript
async function sendMessage() {
  // ... 创建临时消息 ...
  chatStore.addMessage(chatStore.currentConversation, tempMsg);
  
  // ... 清理输入 ...
  
  try {
    await wsManager.sendMessageWithId(...);
    // 不再手动替换，完全依赖 WebSocket 的 updateMessage
  } catch (error) {
    // 只在失败时更新状态
    const msgs = chatStore.messages[chatStore.currentConversation];
    const idx = msgs.findIndex(m => m.client_message_id === clientMessageId);
    if (idx !== -1) {
      msgs[idx]._sending = false;
      msgs[idx]._error = true;
    }
  }
}
```

### 步骤3：优化 updateMessage 函数
确保 `updateMessage` 不会在找不到消息时添加新消息（避免重复）：
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
  // 移除 else 分支，不再添加新消息
}
```

## 涉及文件
1. `frontend/src/views/Chat.vue` - 修改 CSS 样式和 sendMessage 函数
2. `frontend/src/stores/chat.js` - 修改 updateMessage 函数
