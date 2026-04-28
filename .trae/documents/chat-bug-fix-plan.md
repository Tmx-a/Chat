# 实时聊天功能 Bug 修复计划

## 问题分析

### 问题1：好友在线状态始终显示离线

**根本原因**：
1. WebSocket 使用 `AuthMiddlewareStack` 进行认证，这是基于 Django Session 的认证方式
2. 前端通过 URL 参数传递 JWT Token：`/ws/chat/?token=xxx`
3. `AuthMiddlewareStack` 不会解析 URL 中的 JWT Token，导致 `self.scope['user']` 始终是匿名用户
4. 匿名用户在 `connect()` 中被拒绝连接，`is_online` 状态从未被设置为 `True`

### 问题2：发送消息后对话框不显示内容

**根本原因**：
1. 由于 WebSocket 认证失败，连接被关闭
2. 消息无法通过 WebSocket 发送和接收
3. 即使调用 `wsManager.sendMessage()`，WebSocket 连接已断开，消息无法送达

---

## 修复方案

### 修复1：实现 JWT WebSocket 认证中间件

创建自定义中间件解析 URL 中的 JWT Token：

```
backend/chat/middleware.py  # 新建文件
```

中间件逻辑：
1. 从 URL query string 中提取 `token` 参数
2. 使用 `djangorestframework_simplejwt` 验证 Token
3. 将验证后的用户注入到 `scope['user']`

### 修复2：更新 ASGI 配置

修改 `asgi.py`，使用自定义的 JWT 认证中间件替代 `AuthMiddlewareStack`。

### 修复3：添加用户状态广播

当用户上线/下线时，广播状态变化给其好友：
1. 在 `connect()` 中广播上线状态
2. 在 `disconnect()` 中广播下线状态
3. 前端监听状态变化并更新好友列表

### 修复4：前端优化

1. 监听用户状态变化消息
2. 更新好友列表中的在线状态
3. 添加 WebSocket 连接状态提示

---

## 实施步骤

### 步骤1：创建 JWT WebSocket 认证中间件
- 新建 `backend/chat/middleware.py`
- 实现 `JWTAuthMiddleware` 类

### 步骤2：更新 ASGI 配置
- 修改 `backend/chat_project/asgi.py`
- 使用 `JWTAuthMiddlewareStack` 替代 `AuthMiddlewareStack`

### 步骤3：添加用户状态广播功能
- 修改 `backend/chat/consumers.py`
- 在 `connect()` 中广播上线状态
- 在 `disconnect()` 中广播下线状态

### 步骤4：前端监听状态变化
- 修改 `frontend/src/utils/websocket.js`
- 添加用户状态变化消息处理
- 修改 `frontend/src/stores/chat.js`
- 添加更新好友状态的方法

### 步骤5：验证修复
- 测试 WebSocket 连接是否成功
- 测试在线状态是否正确显示
- 测试消息发送和接收是否正常
