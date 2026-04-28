# 本地实时聊天项目 - 可行性分析与实施计划

## 一、可行性分析

### 技术栈评估

| 技术 | 可行性 | 说明 |
|------|--------|------|
| Python + Django | ✅ 完全可行 | Django 是成熟的 Web 框架，生态丰富 |
| Django Channels | ✅ 完全可行 | 基于 WebSocket 实现实时通信，是 Django 官方推荐的实时方案 |
| Vue 3 + Element Plus | ✅ 完全可行 | Vue 3 组合式 API + Element Plus 组件库，适合快速构建聊天 UI |
| MySQL | ✅ 完全可行 | Django 原生支持 MySQL，用于持久化聊天记录和用户数据 |

### 结论：**完全可行**

Django Channels 提供 WebSocket 支持，可以实现实时消息推送；Vue 3 + Element Plus 可以快速构建现代化的聊天界面；MySQL 用于数据持久化。这套技术栈搭配成熟、社区支持好、文档丰富。

---

## 二、系统架构

```
┌─────────────────────────────────────────────────┐
│                   前端 (Vue 3)                   │
│  ┌───────────┐  ┌───────────┐  ┌──────────────┐ │
│  │ 登录/注册  │  │  聊天界面  │  │  好友/群组   │ │
│  └─────┬─────┘  └─────┬─────┘  └──────┬───────┘ │
│        │              │               │          │
│        └──────────────┼───────────────┘          │
│                       │ WebSocket / HTTP          │
└───────────────────────┼──────────────────────────┘
                        │
┌───────────────────────┼──────────────────────────┐
│                后端 (Django)                      │
│  ┌────────────┐  ┌───┴────┐  ┌───────────────┐  │
│  │ REST API   │  │Channels│  │  认证系统      │  │
│  │ (DRF)      │  │(WS)    │  │  (JWT)        │  │
│  └─────┬──────┘  └───┬────┘  └───────┬───────┘  │
│        └──────────────┼───────────────┘          │
│                       │                          │
│              ┌────────┴────────┐                 │
│              │     MySQL       │                 │
│              └─────────────────┘                 │
└──────────────────────────────────────────────────┘
```

---

## 三、功能模块

### 核心功能
1. **用户系统**：注册、登录、JWT 认证
2. **一对一聊天**：实时私聊消息收发
3. **群组聊天**：创建群组、群消息收发
4. **好友管理**：添加好友、好友列表
5. **消息记录**：历史消息持久化与加载
6. **在线状态**：用户上下线状态展示

### 扩展功能（可选）
7. 消息已读/未读状态
8. 图片/文件发送
9. 消息通知提醒
10. 用户头像上传

---

## 四、项目结构

### 后端项目结构
```
backend/
├── chat_project/          # Django 项目配置
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py            # ASGI 配置（WebSocket 入口）
│   └── wsgi.py
├── users/                 # 用户应用
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── chat/                  # 聊天应用
│   ├── models.py          # 消息、会话模型
│   ├── consumers.py       # WebSocket 消费者
│   ├── routing.py         # WebSocket 路由
│   ├── views.py           # REST API 视图
│   ├── serializers.py
│   └── urls.py
├── manage.py
└── requirements.txt
```

### 前端项目结构
```
frontend/
├── src/
│   ├── api/               # API 请求封装
│   ├── assets/            # 静态资源
│   ├── components/        # 公共组件
│   │   ├── ChatMessage.vue
│   │   ├── ContactList.vue
│   │   └── UserStatus.vue
│   ├── views/             # 页面视图
│   │   ├── Login.vue
│   │   ├── Register.vue
│   │   └── Chat.vue
│   ├── stores/            # Pinia 状态管理
│   ├── router/            # 路由配置
│   ├── utils/             # 工具函数（WebSocket 封装等）
│   ├── App.vue
│   └── main.js
├── package.json
└── vite.config.js
```

---

## 五、数据库设计

### 用户表 (User) - 使用 Django 内置 + 扩展
- id: 主键
- username: 用户名
- password: 密码（加密）
- avatar: 头像 URL
- is_online: 是否在线
- last_seen: 最后在线时间

### 好友关系表 (Friendship)
- id: 主键
- user: 外键 → User
- friend: 外键 → User
- created_at: 创建时间

### 会话表 (Conversation)
- id: 主键
- type: 会话类型（private / group）
- name: 会话名称（群聊用）
- created_at: 创建时间

### 会话成员表 (ConversationMember)
- id: 主键
- conversation: 外键 → Conversation
- user: 外键 → User
- joined_at: 加入时间

### 消息表 (Message)
- id: 主键
- conversation: 外键 → Conversation
- sender: 外键 → User
- content: 消息内容
- message_type: 消息类型（text / image / file）
- created_at: 发送时间
- is_read: 是否已读

---

## 六、实施步骤

### 第一阶段：项目初始化
1. 创建 Django 后端项目，安装依赖（Django、djangorestframework、channels、mysqlclient）
2. 创建 Vue 3 前端项目，安装依赖（Element Plus、Pinia、Vue Router、axios）
3. 配置 MySQL 数据库连接
4. 配置 Django Channels（ASGI、Redis 作为 Channel Layer）

### 第二阶段：用户系统
5. 实现后端用户注册/登录 API（使用 JWT 认证）
6. 实现前端登录/注册页面
7. 配置前端路由守卫和 axios 拦截器

### 第三阶段：实时通信核心
8. 实现 Django Channels WebSocket 消费者
9. 配置 WebSocket 路由
10. 前端封装 WebSocket 连接管理类
11. 实现一对一聊天消息收发

### 第四阶段：聊天功能完善
12. 实现好友管理（添加、列表）
13. 实现群组聊天功能
14. 实现历史消息加载
15. 实现在线状态展示

### 第五阶段：UI 优化与测试
16. 优化聊天界面（消息气泡、时间显示等）
17. 消息通知提醒
18. 整体联调测试

---

## 七、关键依赖

### 后端 (requirements.txt)
```
Django>=4.2
djangorestframework>=3.14
djangorestframework-simplejwt>=5.3
channels>=4.0
channels-redis>=4.2
mysqlclient>=2.2
django-cors-headers>=4.3
```

### 前端 (package.json 核心依赖)
```
vue@3
vue-router@4
pinia
element-plus
axios
```

### 额外服务
- **Redis**：Django Channels 的 Channel Layer 后端（必需，用于 WebSocket 消息分发）

---

## 八、注意事项

1. **Redis 依赖**：Django Channels 需要 Redis 作为消息代理，本地开发需安装 Redis 服务
2. **CORS 配置**：前后端分离开发需配置 django-cors-headers
3. **ASGI 部署**：生产环境需使用 Daphne 或 Uvicorn 作为 ASGI 服务器
4. **WebSocket 安全**：生产环境建议使用 WSS（WebSocket Secure）
5. **MySQL 字符集**：建议使用 utf8mb4 以支持 emoji 表情
