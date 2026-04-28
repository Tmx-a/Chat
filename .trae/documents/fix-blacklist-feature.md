# 黑名单功能修复计划

## 问题分析

当前黑名单功能存在以下问题：
1. **无法取消拉黑**：前端没有黑名单列表UI，无法查看和移除黑名单用户
2. **会话未隐藏**：拉黑后，与被拉黑者的会话仍然显示在消息列表中
3. **消息未拦截**：拉黑后仍然可以互相发送消息，黑名单没有生效

## 修复方案

### 第一阶段：后端修复

#### 1. WebSocket消息发送黑名单检查
- 修改 `chat/consumers.py` 的 `save_message` 方法
- 发送消息前检查发送者是否被接收者拉黑
- 如果被拉黑，返回错误消息，不保存消息

#### 2. 拉黑时隐藏会话
- 修改 `chat/views.py` 的 `BlockUserView`
- 拉黑时查找与被拉黑者的私聊会话
- 将会话标记为隐藏（is_hidden=True）

#### 3. 返回黑名单状态
- 修改会话列表API，返回与每个会话用户之间的黑名单状态
- 或添加单独的API检查黑名单状态

### 第二阶段：前端修复

#### 4. 添加黑名单列表UI
- 在设置菜单添加"黑名单"入口
- 创建黑名单列表对话框
- 显示被拉黑用户列表，支持取消拉黑

#### 5. 拉黑后更新UI
- 拉黑成功后从好友列表移除
- 从会话列表移除相关会话
- 显示成功提示

#### 6. 消息发送拦截
- 发送消息前检查是否被对方拉黑
- 如果被拉黑，显示提示信息，禁止发送

## 实现步骤

### Step 1: 后端 - WebSocket黑名单检查
修改 `backend/chat/consumers.py`：
- 在 `save_message` 方法中添加黑名单检查
- 检查发送者是否在接收者的黑名单中
- 如果被拉黑，返回错误信息

### Step 2: 后端 - 拉黑时隐藏会话
修改 `backend/chat/views.py`：
- 在 `BlockUserView` 中查找私聊会话
- 设置 `is_hidden=True`

### Step 3: 前端 - 黑名单列表UI
修改 `frontend/src/views/Chat.vue`：
- 添加黑名单菜单入口
- 创建黑名单列表对话框
- 实现取消拉黑功能

### Step 4: 前端 - 拉黑后UI更新
修改 `frontend/src/views/Chat.vue`：
- `blockFriend` 函数中更新会话列表
- 移除被拉黑者的会话

### Step 5: 前端 - 消息发送检查
修改 `frontend/src/views/Chat.vue`：
- 发送消息前检查黑名单状态
- 显示被拉黑提示

## 涉及文件

- `backend/chat/consumers.py` - WebSocket消息处理
- `backend/chat/views.py` - 拉黑API
- `backend/chat/serializers.py` - 可能需要添加黑名单状态字段
- `frontend/src/views/Chat.vue` - 主要UI修改
- `frontend/src/api/modules.js` - 可能需要添加API
