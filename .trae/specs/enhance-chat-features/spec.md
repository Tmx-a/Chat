# 聊天应用功能增强 Spec

## Why
当前聊天应用仅具备基础的私聊、群聊和好友功能，缺乏消息状态追踪、富媒体支持、用户体验优化等核心功能，无法满足现代即时通讯应用的完整需求。

## What Changes
- 添加消息已读回执功能
- 支持图片/文件发送
- 用户头像上传功能
- 好友申请审核机制
- 消息撤回功能
- 输入状态提示
- 用户搜索发现
- 群组管理功能
- 深色模式
- 消息搜索
- 消息通知
- 修改密码
- 账号注销

## Impact
- Affected specs: 消息系统、用户系统、好友系统、群组系统
- Affected code: 
  - 后端: users/models.py, chat/models.py, chat/consumers.py, chat/views.py
  - 前端: Chat.vue, stores/chat.js, utils/websocket.js

---

## ADDED Requirements

### Requirement: 消息已读回执
系统 SHALL 提供消息已读状态追踪功能。

#### Scenario: 发送方查看已读状态
- **WHEN** 用户发送消息后
- **THEN** 消息显示已读或未读状态
- **AND** 已读消息显示已读标记

#### Scenario: 接收方阅读消息
- **WHEN** 用户打开会话查看消息
- **THEN** 系统自动将消息标记为已读
- **AND** 通知发送方消息已读

### Requirement: 图片/文件发送
系统 SHALL 支持发送图片和文件。

#### Scenario: 发送图片
- **WHEN** 用户选择图片并发送
- **THEN** 图片上传至服务器
- **AND** 在聊天界面显示图片预览

#### Scenario: 发送文件
- **WHEN** 用户选择文件并发送
- **THEN** 文件上传至服务器
- **AND** 在聊天界面显示文件卡片（文件名、大小、下载链接）

### Requirement: 用户头像上传
系统 SHALL 允许用户上传自定义头像。

#### Scenario: 上传头像
- **WHEN** 用户在设置中选择图片作为头像
- **THEN** 图片上传并保存
- **AND** 用户头像立即更新显示

### Requirement: 好友申请审核
系统 SHALL 实现好友申请审核机制。

#### Scenario: 发送好友申请
- **WHEN** 用户A向用户B发送好友申请
- **THEN** 用户B收到好友申请通知
- **AND** 双方未成为好友直到用户B同意

#### Scenario: 同意好友申请
- **WHEN** 用户B同意好友申请
- **THEN** 双方成为好友
- **AND** 互相出现在好友列表

#### Scenario: 拒绝好友申请
- **WHEN** 用户B拒绝好友申请
- **THEN** 申请被拒绝
- **AND** 用户A收到拒绝通知（可选）

### Requirement: 消息撤回
系统 SHALL 允许用户撤回已发送的消息。

#### Scenario: 撤回消息
- **WHEN** 用户在2分钟内撤回消息
- **THEN** 消息从双方聊天记录中删除
- **AND** 显示"XX撤回了一条消息"提示

#### Scenario: 超时撤回
- **WHEN** 用户尝试撤回超过2分钟的消息
- **THEN** 系统拒绝撤回操作
- **AND** 提示"消息已超过撤回时限"

### Requirement: 输入状态提示
系统 SHALL 显示对方的输入状态。

#### Scenario: 对方正在输入
- **WHEN** 用户A正在输入消息
- **THEN** 用户B看到"正在输入..."提示
- **AND** 输入停止后提示消失

### Requirement: 用户搜索发现
系统 SHALL 支持按用户名搜索用户。

#### Scenario: 搜索用户
- **WHEN** 用户输入关键词搜索
- **THEN** 显示匹配的用户列表
- **AND** 可直接发送好友申请

### Requirement: 群组管理
系统 SHALL 提供群组管理功能。

#### Scenario: 群主转让
- **WHEN** 群主将群主身份转让给其他成员
- **THEN** 新群主获得管理权限
- **AND** 原群主变为普通成员

#### Scenario: 移除群成员
- **WHEN** 群主移除某成员
- **THEN** 该成员退出群聊
- **AND** 无法再查看群消息

#### Scenario: 退出群聊
- **WHEN** 普通成员退出群聊
- **THEN** 该成员退出群聊
- **AND** 群聊历史消息保留

### Requirement: 深色模式
系统 SHALL 支持深色模式切换。

#### Scenario: 切换主题
- **WHEN** 用户切换深色/浅色模式
- **THEN** 界面颜色主题立即切换
- **AND** 用户偏好被保存

### Requirement: 消息搜索
系统 SHALL 支持搜索历史消息。

#### Scenario: 搜索消息
- **WHEN** 用户输入关键词搜索
- **THEN** 显示包含关键词的消息列表
- **AND** 可点击跳转到原消息位置

### Requirement: 消息通知
系统 SHALL 提供消息通知功能。

#### Scenario: 浏览器通知
- **WHEN** 用户收到新消息且页面不在焦点
- **THEN** 浏览器显示通知弹窗
- **AND** 点击通知跳转到对应会话

#### Scenario: 声音提醒
- **WHEN** 用户收到新消息
- **THEN** 播放提示音（可设置关闭）

### Requirement: 修改密码
系统 SHALL 允许用户修改密码。

#### Scenario: 修改密码
- **WHEN** 用户输入旧密码和新密码
- **THEN** 验证旧密码正确后更新密码
- **AND** 提示修改成功

### Requirement: 账号注销
系统 SHALL 允许用户注销账号。

#### Scenario: 注销账号
- **WHEN** 用户确认注销账号
- **THEN** 删除用户所有数据
- **AND** 账号无法恢复
