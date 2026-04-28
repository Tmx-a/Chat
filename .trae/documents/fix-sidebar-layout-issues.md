# 修复侧边栏和布局问题 + 整体优化

## 问题分析

### 问题1：登录后显示灰色阴影，需要点击才显示侧边栏

**根本原因**：`sidebarCollapsed` 初始化为 `ref(window.innerWidth <= 768)`，但 `mobile-overlay` 的显示逻辑有误：

```html
<div v-if="sidebarCollapsed" class="mobile-overlay" @click="sidebarCollapsed = false"></div>
```

当 `sidebarCollapsed = true` 时，overlay 显示。但 `.mobile-overlay` 默认 `display: none`，只在 `@media (max-width: 768px)` 时 `display: block`。

**问题在于**：侧边栏的 `.expanded` 类逻辑是 `expanded: !sidebarCollapsed`，即 `sidebarCollapsed = true` 时没有 `expanded` 类。但在桌面端，侧边栏没有 `position: fixed`，所以即使没有 `expanded` 类，侧边栏仍然正常显示。

**但是**：overlay 在桌面端虽然 `display: none`，但 `sidebarCollapsed = true` 意味着在移动端选择会话后 `sidebarCollapsed` 被设为 `true`，然后 resize 事件只在 `> 768` 时才重置为 `false`。如果用户在桌面端首次加载时窗口宽度恰好 ≤ 768，就会出现灰色遮罩。

**更关键的问题**：在桌面端（>768px），`sidebarCollapsed` 如果为 `true`，虽然 overlay 不显示（`display: none`），但侧边栏的 `expanded` 类为 `false`。由于桌面端侧边栏没有 `position: fixed`，它仍然正常显示。所以桌面端实际上没有视觉问题。

**但如果用户浏览器窗口 ≤ 768px**（如小笔记本、分屏等），`sidebarCollapsed = true`，overlay 显示，侧边栏隐藏在左侧，用户需要点击 overlay 才能看到侧边栏。这是预期行为，但用户觉得不好。

### 问题2：聊天对话框布局问题

需要检查消息气泡、输入区域等布局是否正确。

## 修复方案

### 1. 修复侧边栏默认状态
- 桌面端（>768px）默认 `sidebarCollapsed = false`
- 只在真正移动端（<768px）时默认折叠
- 修复 overlay 逻辑：overlay 应该只在移动端且侧边栏展开时显示（用于点击关闭），而不是在侧边栏折叠时显示

### 2. 修复 overlay 显示逻辑
当前：`v-if="sidebarCollapsed"` → 显示 overlay 当侧边栏折叠时
正确：overlay 应该在移动端且侧边栏展开时显示，用于点击关闭侧边栏

### 3. 整体代码优化
- 检查并修复所有布局问题
- 清理冗余代码
- 确保所有功能正常工作

## 实现步骤

### Step 1: 修复侧边栏和overlay逻辑
- 修改 `sidebarCollapsed` 初始化为 `false`（桌面端默认展开）
- 修改 overlay 的 v-if 条件：`v-if="!sidebarCollapsed && isMobile"` 或使用 CSS 控制
- 修改侧边栏类名逻辑：桌面端始终显示，移动端通过 expanded 控制
- 添加 `isMobile` 计算属性

### Step 2: 修复聊天区域布局
- 检查消息气泡样式
- 检查输入区域样式
- 确保消息列表正确滚动

### Step 3: 整体优化
- 清理冗余CSS
- 修复可能的样式冲突
- 确保深色模式正常
