# UI/UX 完善与现代化美化 Spec

## Why
当前聊天应用功能基本完善，但UI/UX存在多处严重影响使用体验的问题（单行输入框无法换行、缺少加载状态、颜色不统一、无响应式等），且视觉风格不够现代化简洁，需要系统性优化。

## What Changes
- 消息输入框改为可自动增高的textarea，支持Ctrl+Enter发送
- 添加CSS变量统一管理颜色主题，替代40+处dark-mode覆盖
- 添加消息动画、会话切换动画、列表项动画
- 合并连续同一人消息，减少视觉噪音
- 添加初始加载骨架屏和会话切换loading
- 支持粘贴图片和拖拽文件发送
- 添加消息草稿保存（切换会话保留输入内容）
- 修复右键菜单边界溢出
- 添加移动端响应式布局（侧边栏可折叠）
- 统一颜色、间距、字号体系
- 添加新消息提示音
- 搜索结果高亮关键词
- 图片消息添加loading占位

## Impact
- Affected specs: 全局UI/UX
- Affected code: Chat.vue（主要）、style.css、Login.vue、Register.vue、App.vue

## ADDED Requirements

### Requirement: 多行消息输入
系统 SHALL 提供可自动增高的textarea作为消息输入框，支持Enter换行和Ctrl+Enter发送。

#### Scenario: 输入多行消息
- **WHEN** 用户按Enter键
- **THEN** 输入框换行而非发送消息
- **WHEN** 用户按Ctrl+Enter
- **THEN** 发送消息

### Requirement: CSS变量主题系统
系统 SHALL 使用CSS变量统一管理颜色主题，支持一键切换深色/浅色模式。

#### Scenario: 切换深色模式
- **WHEN** 用户切换深色模式
- **THEN** 所有颜色通过CSS变量自动切换
- **AND** 无需40+处单独覆盖样式

### Requirement: 消息动画
系统 SHALL 为消息列表添加进入动画和会话切换过渡效果。

#### Scenario: 收到新消息
- **WHEN** 新消息到达
- **THEN** 消息以滑入+淡入动画出现

### Requirement: 连续消息合并
系统 SHALL 合并连续同一人发送的消息，只显示一次头像和名称。

#### Scenario: 连续发送消息
- **WHEN** 同一人连续发送多条消息
- **THEN** 只在第一条消息显示头像和名称
- **AND** 后续消息气泡紧密排列

### Requirement: 加载状态
系统 SHALL 在数据加载时显示骨架屏或loading指示。

#### Scenario: 首次加载
- **WHEN** 页面首次加载
- **THEN** 显示骨架屏而非空白
- **WHEN** 切换会话加载消息
- **THEN** 显示loading指示

### Requirement: 粘贴图片和拖拽文件
系统 SHALL 支持Ctrl+V粘贴图片和拖拽文件到聊天窗口发送。

#### Scenario: 粘贴图片
- **WHEN** 用户在输入框中Ctrl+V粘贴图片
- **THEN** 图片自动上传并发送

#### Scenario: 拖拽文件
- **WHEN** 用户拖拽文件到聊天区域
- **THEN** 文件自动上传并发送

### Requirement: 消息草稿
系统 SHALL 在切换会话时保存当前输入内容，切回时恢复。

#### Scenario: 保存草稿
- **WHEN** 用户在会话A输入了文字但未发送
- **AND** 切换到会话B
- **THEN** 会话A的输入内容被保存
- **WHEN** 切回会话A
- **THEN** 输入内容恢复

### Requirement: 右键菜单边界检测
系统 SHALL 检测右键菜单是否超出视口边界并自动调整位置。

### Requirement: 响应式布局
系统 SHALL 在小屏幕设备上支持侧边栏折叠。

#### Scenario: 移动端使用
- **WHEN** 屏幕宽度小于768px
- **THEN** 侧边栏默认折叠
- **AND** 点击汉堡菜单按钮展开

### Requirement: 新消息提示音
系统 SHALL 在收到新消息时播放提示音。

### Requirement: 搜索高亮
系统 SHALL 在消息搜索结果中高亮关键词。

### Requirement: 图片加载占位
系统 SHALL 为图片消息显示加载占位符和加载失败处理。
