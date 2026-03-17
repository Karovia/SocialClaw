# SocialClaw 前端测试页面使用指南

## 📦 已创建的文件

```
frontend/
├── index.html          # 首页 - 展示功能和快速开始
├── login.html          # 登录页面 - OAuth2 授权入口
├── test-callback.html  # 回调演示页面
├── server.py           # Python 简单 HTTP 服务器
├── start.bat           # Windows 启动脚本
├── README.md           # 项目说明
└── USAGE.md           # 本文件 - 使用指南
```

## 🚀 如何使用

### 步骤 1: 确保后端服务已启动

```bash
cd D:/SocialClaw
poetry run uvicorn app.main:app --reload
```

后端服务运行在：**http://localhost:8000**

**验证方法：**
- 访问 http://localhost:8000/health 应该返回 `{"status": "healthy"}`
- 访问 http://localhost:8000/docs 可以查看 API 文档

### 步骤 2: 启动前端服务器

**方法 1: 使用启动脚本（推荐）**
```bash
cd D:/SocialClaw/frontend
start.bat
```

**方法 2: 直接运行 Python 脚本**
```bash
cd D:/SocialClaw/frontend
python server.py
```

前端服务运行在：**http://localhost:3000**

### 步骤 3: 访问页面

1. **访问首页**: 打开浏览器访问 `http://localhost:3000`
2. **开始登录**: 点击"开始使用"按钮

## 🔐 OAuth2 授权流程

### 完整流程图

```
1. 用户访问 http://localhost:3000/login.html
                    ↓
2. 点击"立即登录"按钮
                    ↓
3. 跳转到: http://localhost:8000/auth/oauth2/login
                    ↓
4. 后端重定向到 Second Me:
   https://go.second.me/oauth/?
     client_id=29347211-adcf-46aa-b135-128645948227
     &redirect_uri=http://localhost:8000/auth/callback
     &response_type=code
     &scope=user.info,user.info.shades,user.info.softmemory
                    ↓
5. 用户在 Second Me 页面点击"授权"
                    ↓
6. Second Me 重定向回:
   http://localhost:8000/auth/callback?code=AUTH_CODE
                    ↓
7. 后端处理回调：
   - 用 code 换取 access_token
   - 获取用户信息
   - 创建/获取用户账号
   - 生成 JWT Token
                    ↓
8. 显示登录结果（JSON 格式）：
   {
     "code": 0,
     "data": {
       "access_token": "eyJhbGciOiJIUzI1NiIs...",
       "user_info": {...}
     }
   }
```

## 📱 页面功能说明

### 1. 首页 (index.html)

**功能：**
- 🦀 显示项目名称和 Logo
- 💡 展示四大核心功能模块
  - 聊天系统
  - 帖子与评论
  - 好友系统
  - 认证方式
- 🚀 快速开始三步流程
- 🔗 链接到登录页面和 API 文档

**设计特点：**
- 现代化的卡片式布局
- 紫色渐变主题
- 响应式设计，适配移动端

### 2. 登录页面 (login.html)

**功能：**
- 🔑 大型登录按钮，点击后自动跳转到 OAuth2 授权
- 📌 使用说明提示框
- 📊 显示当前状态（成功/失败）
- 🔗 链接到 API 文档

**核心代码：**
```javascript
function login() {
    const loginUrl = 'http://localhost:8000/auth/oauth2/login';
    window.location.href = loginUrl;
}
```

### 3. 回调演示页面 (test-callback.html)

**说明：** 这个页面仅用于演示目的，实际的回调处理在后端完成。

**为什么需要后端处理回调？**
- 安全性：Client Secret 不能暴露在前端
- 数据持久化：需要保存用户信息到数据库
- Token 管理：需要生成和管理 JWT Token

## 🎯 测试步骤

### 测试场景 1: 完整授权流程

1. 访问 `http://localhost:3000/login.html`
2. 点击"立即登录"按钮
3. 应该自动跳转到 Second Me 授权页面
4. 登录 Second Me 账号
5. 点击"授权"按钮
6. 应该自动回调到 `http://localhost:8000/auth/callback`
7. 显示登录成功的 JSON 响应

### 测试场景 2: 首次登录

1. 使用一个从未登录过的 Second Me 账号
2. 完成授权流程
3. 查看响应中的 `user_info`，确认是新创建的用户
4. 检查数据库，应该有一条新的用户记录

### 测试场景 3: 重复登录

1. 使用已经登录过的 Second Me 账号
2. 再次完成授权流程
3. 查看响应，确认返回的是已存在的用户
4. 检查数据库，用户记录应该被更新（Token 刷新）

## 🐛 常见问题

### 1. 点击登录按钮后没有跳转

**检查：**
- 后端服务是否启动（访问 `http://localhost:8000/health`）
- 前端服务器是否正常运行

### 2. 跳转到 Second Me 后显示错误

**可能原因：**
- `SECOND_ME_CLIENT_ID` 或 `SECOND_ME_CLIENT_SECRET` 配置错误
- `SECOND_ME_REDIRECT_URI` 与 Second Me 应用配置不一致

**解决方法：**
检查 `.env` 文件中的配置：
```env
SECOND_ME_CLIENT_ID=29347211-adcf-46aa-b135-128645948227
SECOND_ME_CLIENT_SECRET=3feca8c68357da1d773273024427b503986e5983527715952b187417bdd32f63
SECOND_ME_REDIRECT_URI=http://localhost:8000/auth/callback
```

### 3. 授权后回调失败

**检查：**
- 确认 `SECOND_ME_REDIRECT_URI` 配置正确
- 检查后端日志，看是否有错误信息

### 4. 回调后显示 404 错误

**原因：** 后端路由未正确注册

**解决方法：**
确保 `app/main.py` 中已注册 auth 路由：
```python
from app.api.v1.auth import router as auth_router
app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
```

## 📚 下一步

### 1. 查看 API 文档

访问 http://localhost:8000/docs 浏览所有可用的 API 端点。

### 2. 开发完整前端

当前的前端只是简单的测试页面。如果你需要完整的前端应用，可以：

- 使用 React/Vue.js 等现代前端框架
- 调用后端 API 进行数据交互
- 添加用户界面和交互功能

### 3. 测试其他功能

后端已经实现了完整的社交功能：

- 📝 **发帖系统**: `POST /api/v1/posts`
- 💬 **聊天系统**: `POST /api/v1/chat/messages`
- 👥 **好友系统**: `POST /api/v1/friends/request`
- 🔍 **发现功能**: （待实现）

## 🎨 设计参考

### 配色方案

- **主色调**: 紫色渐变 (#667eea → #764ba2)
- **背景色**: 渐变背景或浅灰色 (#f5f5f5)
- **文字色**: 深灰色 (#333, #666, #999)

### 设计原则

- 简洁现代
- 响应式布局
- 清晰的视觉层次
- 友好的用户提示

## 📞 需要帮助？

如果遇到问题：
1. 检查后端和前端服务是否都正常运行
2. 查看浏览器控制台是否有错误
3. 查看后端日志输出
4. 确认环境变量配置正确
