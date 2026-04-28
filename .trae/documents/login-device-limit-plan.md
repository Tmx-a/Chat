# 登录设备限制功能实现计划

## 一、需求分析

### 当前问题
- 使用 JWT 无状态认证，token 一旦签发无法撤销
- 用户可以在多个设备/浏览器同时登录
- 无法管理已登录设备或踢出其他设备

### 目标功能
1. **单设备登录限制** - 可选配置，限制同一账号只能在一个设备登录
2. **多设备管理** - 查看当前已登录的所有设备
3. **踢出设备** - 可以远程踢出其他已登录设备
4. **登录通知** - 新设备登录时通知用户

---

## 二、技术方案

### 2.1 后端实现

#### 2.1.1 创建 UserSession 模型 (users/models.py)
```python
class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_id = models.CharField(max_length=64, unique=True)  # 唯一会话ID
    refresh_token = models.CharField(max_length=512)  # 存储refresh token用于撤销
    device_info = models.CharField(max_length=256)  # 设备信息 (User-Agent)
    ip_address = models.CharField(max_length=45)  # IP地址
    last_activity = models.DateTimeField(auto_now=True)  # 最后活跃时间
    created_at = models.DateTimeField(auto_now_add=True)  # 登录时间
    is_active = models.BooleanField(default=True)  # 会话是否有效

    class Meta:
        db_table = 'user_sessions'
        ordering = ['-created_at']
```

#### 2.1.2 自定义登录视图 (users/views.py)
- 继承 `TokenObtainPairView`
- 登录成功后创建 UserSession 记录
- 如果启用单设备限制，踢出其他设备
- 返回 session_id 给前端

#### 2.1.3 自定义 JWT 认证后端 (users/authentication.py)
- 继承 `JWTAuthentication`
- 验证 token 时检查对应的 session 是否有效
- 无效则拒绝访问

#### 2.1.4 新增 API 接口
| 接口 | 方法 | 功能 |
|------|------|------|
| `/users/sessions/` | GET | 获取已登录设备列表 |
| `/users/sessions/<id>/` | DELETE | 踢出指定设备 |
| `/users/sessions/logout-all/` | POST | 踢出所有其他设备 |

#### 2.1.5 WebSocket 会话验证 (chat/middleware.py)
- 连接时验证 session 是否有效
- 无效则断开连接

#### 2.1.6 配置项 (settings.py)
```python
LOGIN_SETTINGS = {
    'SINGLE_DEVICE_LOGIN': False,  # 是否单设备登录
    'MAX_DEVICES': 5,  # 最大同时登录设备数
}
```

### 2.2 前端实现

#### 2.2.1 设备管理界面 (Chat.vue 或新组件)
- 显示已登录设备列表
- 显示设备名称、IP、登录时间、最后活跃时间
- 当前设备标记
- 踢出其他设备按钮

#### 2.2.2 登录流程修改
- 存储 session_id 到 localStorage
- 每次请求携带 session_id

#### 2.2.3 被踢出处理
- 收到 401 错误且提示"会话已失效"时
- 清除本地数据，跳转登录页
- 显示提示信息"您的账号在其他设备登录"

---

## 三、实现步骤

### 步骤 1: 后端 - 数据模型
1. 在 `users/models.py` 添加 `UserSession` 模型
2. 运行数据库迁移

### 步骤 2: 后端 - 认证系统
1. 创建 `users/authentication.py` 自定义认证后端
2. 创建 `users/views.py` 中的自定义登录视图
3. 更新 `users/urls.py` 路由

### 步骤 3: 后端 - 设备管理 API
1. 创建 `UserSessionListView` - 获取设备列表
2. 创建 `KickSessionView` - 踢出设备
3. 创建 `LogoutAllView` - 踢出所有设备

### 步骤 4: 后端 - WebSocket 验证
1. 修改 `chat/middleware.py` 验证 session

### 步骤 5: 前端 - 设备管理界面
1. 添加 API 方法
2. 创建设备管理对话框
3. 实现踢出功能

### 步骤 6: 前端 - 登录流程
1. 修改登录逻辑存储 session_id
2. 处理被踢出的情况

### 步骤 7: 测试与优化
1. 测试多设备登录
2. 测试踢出功能
3. 测试 WebSocket 断开

---

## 四、文件修改清单

### 后端文件
| 文件 | 操作 |
|------|------|
| `users/models.py` | 新增 UserSession 模型 |
| `users/authentication.py` | 新建 - 自定义认证后端 |
| `users/views.py` | 新增登录视图和设备管理视图 |
| `users/serializers.py` | 新增 UserSessionSerializer |
| `users/urls.py` | 新增路由 |
| `chat/middleware.py` | 修改 WebSocket 认证逻辑 |
| `chat_project/settings.py` | 新增配置项 |

### 前端文件
| 文件 | 操作 |
|------|------|
| `src/api/modules.js` | 新增设备管理 API |
| `src/views/Chat.vue` | 新增设备管理对话框 |
| `src/utils/websocket.js` | 处理 session 验证 |

---

## 五、用户体验流程

### 正常登录
1. 用户输入账号密码登录
2. 后端创建 session 记录，返回 token 和 session_id
3. 前端存储 token 和 session_id

### 查看已登录设备
1. 用户点击设置 -> 设备管理
2. 显示所有已登录设备列表
3. 当前设备有特殊标记

### 踢出其他设备
1. 点击某设备的"踢出"按钮
2. 确认后该设备的 session 失效
3. 被踢设备下次请求时收到 401 错误
4. 被踢设备前端显示"您的账号在其他设备登录"并跳转登录页

### 单设备登录模式
1. 用户在新设备登录
2. 后端自动踢出所有其他设备
3. 旧设备收到通知被踢出

---

## 六、安全考虑

1. **Token 存储**: refresh_token 存储在数据库，用于撤销
2. **Session ID**: 使用 UUID 确保唯一性
3. **设备指纹**: 记录 User-Agent 和 IP 用于识别设备
4. **定期清理**: 自动清理过期的 session 记录
