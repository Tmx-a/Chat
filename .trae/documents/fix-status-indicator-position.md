# 修复在线状态标识位置问题计划

## 问题分析

当前用户头像的在线状态标识（`.status-indicator-dot`）位置不正确，应该在头像的右下角，但现在在右上角偏上。

**当前 HTML 结构：**
```html
<div class="avatar-wrapper" @click="showProfileEdit = true">
  <el-avatar :size="48" class="user-avatar">...</el-avatar>
  <el-dropdown trigger="click" @command="handleStatusChange" @click.stop>
    <span :class="['status-indicator-dot', userStore.user?.status || 'online']" @click.stop></span>
    <template #dropdown>...</template>
  </el-dropdown>
</div>
```

**当前样式：**
```css
.avatar-wrapper {
  position: relative;
}

.status-indicator-dot {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 14px;
  height: 14px;
  border: 2px solid white;
  border-radius: 50%;
  cursor: pointer;
  z-index: 1;
}
```

**问题原因：**
`el-dropdown` 组件会添加额外的包装元素（如 `.el-dropdown` 和 `.el-dropdown__popper`），导致 `.status-indicator-dot` 的 `position: absolute` 不再相对于 `.avatar-wrapper` 定位，而是相对于 `el-dropdown` 的包装元素定位。

## 修复方案

### 方案：调整 HTML 结构
将状态标识移到 `el-dropdown` 外部，使其直接作为 `.avatar-wrapper` 的子元素，同时保持下拉菜单功能：

```html
<div class="avatar-wrapper" @click="showProfileEdit = true">
  <el-avatar :size="48" class="user-avatar">...</el-avatar>
  <el-dropdown trigger="click" @command="handleStatusChange" @click.stop>
    <span class="status-indicator-dot-trigger" @click.stop>
      <span :class="['status-indicator-dot', userStore.user?.status || 'online']"></span>
    </span>
    <template #dropdown>...</template>
  </el-dropdown>
</div>
```

或者更简单的方案：为 `el-dropdown` 添加样式使其不干扰定位：

```css
.avatar-wrapper .el-dropdown {
  position: absolute;
  bottom: 0;
  right: 0;
}
```

## 涉及文件
1. `frontend/src/views/Chat.vue` - 修改样式或 HTML 结构
