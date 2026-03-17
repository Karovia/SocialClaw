# 🔧 问题修复说明

## 问题描述

访问 `http://localhost:8000/auth/oauth2/login` 显示 "Not Found" 错误。

## 问题原因

路由路径错误。正确的路径应该是：
```
http://localhost:8000/api/v1/auth/oauth2/login
```

而不是：
```
http://localhost:8000/auth/oauth2/login
```

## 路由注册说明

在 `app/main.py` 中，auth 路由被注册到 `/api/v1` 前缀：
```python
app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
```

在 `app/api/v1/auth.py` 中，路由本身又定义了 `/auth` 前缀：
```python
router = APIRouter(prefix="/auth", tags=["Auth"])
```

因此完整的路径是：`/api/v1/auth/oauth2/login`

## 修复内容

已修复 `frontend/login.html` 中的登录按钮链接：

**修改前：**
```javascript
const loginUrl = `${API_BASE_URL}/auth/oauth2/login`;
```

**修改后：**
```javascript
const loginUrl = `${API_BASE_URL}/api/v1/auth/oauth2/login`;
```

## ✅ 现在可以正常使用了

### 测试步骤

1. 访问 http://localhost:3000/login.html
2. 点击"立即登录"按钮
3. 应该自动跳转到 Second Me 授权页面
4. 在 Second Me 授权后，会回调到后端
5. 显示登录成功信息

### 可用的 API 端点

**认证相关：**
- `GET /api/v1/auth/oauth2/login` - 跳转到 OAuth2 授权
- `GET /api/v1/auth/callback` - OAuth2 回调处理
- `POST /api/v1/auth/refresh` - 刷新 Token

**用户相关：**
- `GET /api/v1/users/me` - 获取当前用户信息
- `PUT /api/v1/users/profile` - 更新用户资料

**帖子相关：**
- `POST /api/v1/posts` - 发布帖子
- `GET /api/v1/posts/{post_id}` - 获取帖子详情
- `POST /api/v1/posts/{post_id}/comments` - 发表评论

**好友相关：**
- `POST /api/v1/friends/request` - 好友请求
- `POST /api/v1/friends/accept` - 接受好友
- `GET /api/v1/friends` - 好友列表

**聊天相关：**
- `POST /api/v1/chat/messages` - 发送消息
- `GET /api/v1/chat/history` - 聊天历史
- `POST /api/v1/chat/groups` - 创建群聊

## 📚 查看完整 API

访问 http://localhost:8000/docs 浏览所有可用的 API 端点。
