# 修复表情按钮和表情选择器问题计划

## 问题分析

### 问题1：表情按钮图标不直观
当前表情按钮使用 `SemiSelect` 图标，这个图标是一个半圆形选择图标，用户很难联想到这是表情选择按钮。

**当前代码：**
```html
<el-button circle title="表情" @click="showEmojiPicker = !showEmojiPicker">
  <el-icon><SemiSelect /></el-icon>
</el-button>
```

### 问题2：表情选择器背景渲染不完整
表情选择器使用 `el-popover` 组件，但 `.emoji-picker` 样式没有设置背景色和适当的 padding，导致白色背景可能没有完全覆盖表情区域。

**当前样式：**
```css
.emoji-picker {
  display: grid;
  grid-template-columns: repeat(10, 1fr);
  gap: var(--spacing-xs);
}
```

## 修复方案

### 步骤1：更换表情按钮图标
将 `SemiSelect` 图标替换为更直观的表情符号 😊 或使用自定义 SVG 图标：

**方案A：使用表情符号（推荐）**
```html
<el-button circle title="表情" @click="showEmojiPicker = !showEmojiPicker">
  <span class="emoji-btn-icon">😊</span>
</el-button>
```

**方案B：使用 Element Plus 的其他图标**
Element Plus 没有专门的表情图标，所以使用表情符号更直观。

### 步骤2：修复表情选择器背景
为 `.emoji-picker` 添加背景色、padding 和适当的样式：

```css
.emoji-picker {
  display: grid;
  grid-template-columns: repeat(10, 1fr);
  gap: var(--spacing-xs);
  background: var(--color-bg-primary);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  max-height: 200px;
  overflow-y: auto;
}

.emoji-item {
  font-size: var(--font-xl);
  cursor: pointer;
  padding: var(--spacing-sm);
  border-radius: var(--radius-sm);
  text-align: center;
  transition: background var(--transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  min-height: 32px;
}

.emoji-item:hover {
  background: var(--color-bg-hover);
}
```

### 步骤3：添加表情按钮图标样式
为表情按钮图标添加样式，确保表情符号正确显示：

```css
.emoji-btn-icon {
  font-size: 18px;
  line-height: 1;
}
```

## 涉及文件
1. `frontend/src/views/Chat.vue` - 修改表情按钮图标和样式
