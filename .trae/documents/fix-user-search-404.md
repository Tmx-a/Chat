# 修复搜索添加好友"资源不存在"问题

## 问题分析

用户在网站搜索添加好友时，API返回404"资源不存在"。

### 可能原因

1. **URL路由匹配顺序问题**：`users/` 和 `users/search/` 的匹配顺序。Django按顺序匹配URL，如果 `users/` 先匹配，则 `users/search/` 不会被访问到。但查看代码，Django的URL配置是精确匹配的，`path('users/', ...)` 不会匹配 `users/search/`，所以这不是问题。

2. **后端服务未重启**：最可能的原因是后端服务器没有重启，新增的 `UserSearchView` 和URL路由还没有生效。

3. **Vite代理配置问题**：检查代理是否正确转发请求。

4. **请求路径问题**：前端请求 `/api/users/search/?q=xxx`，需要确认后端是否正确处理。

### 实际排查

让我仔细看URL配置：
- `path('users/', UserListView.as_view())` - 匹配 `/api/users/`
- `path('users/search/', UserSearchView.as_view())` - 匹配 `/api/users/search/`

Django的 `path()` 是精确匹配，不会出现 `users/` 匹配到 `users/search/` 的情况。所以路由本身没问题。

**最可能的原因**：后端服务器需要重启以加载新的URL配置。

## 修复方案

1. 确认后端URL路由正确（已确认）
2. 确认前端API请求路径正确（已确认：`/users/search/?q=xxx`）
3. 重启后端服务器
4. 如果仍有问题，检查后端日志确认请求是否到达
