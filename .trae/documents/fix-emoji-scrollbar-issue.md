# 修复表情选择器滚动条问题计划

## 问题分析

当前表情选择器下方出现水平滚动条，用户只希望右侧有垂直滚动条。

**当前样式：**
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
```

**问题原因：**
- 只设置了 `overflow-y: auto`，没有设置 `overflow-x`
- 表情选择器的内容可能超出容器宽度，导致出现水平滚动条

## 修复方案

### 步骤1：隐藏水平滚动条
为 `.emoji-picker` 添加 `overflow-x: hidden`，只保留垂直滚动：

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
  overflow-x: hidden;
}
```

### 步骤2：确保内容不超出宽度
为 `.emoji-item` 移除 `min-width`，使用固定宽度确保不会超出容器：

```css
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
  width: 100%;
  aspect-ratio: 1;
}
```

## 涉及文件
1. `frontend/src/views/Chat.vue` - 修改 `.emoji-picker` 和 `.emoji-item` 样式
