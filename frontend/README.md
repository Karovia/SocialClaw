# SocialClaw 前端测试页面

这是一个简单的前端测试页面，用于测试 Second Me OAuth2 授权流程。

## 🚀 快速开始

### 1. 启动后端服务

```
cd D:/SocialClaw
poetry run uvicorn app.main:app --reload
```

后端服务将运行在 `http://localhost:8000`

### 2. 启动前端服务器

```
cd D:/SocialClaw/frontend
python server.py
```

前端服务将运行在 `http://localhost:3000`

### 3. 访问页面

打开浏览器访问：

- **首页**: `http://localhost:3000`
- **登录页**: `http://localhost:3000/login.html`

## 📱 使用流程

1. 访问 `http://localhost:3000/login.html`
2. 点击"立即登录"按钮
3. 自动跳转到 Second Me 授权页面
4. 在 Second Me 页面点击"授权"
5. 自动回调到 SocialClaw 后端
6. 显示登录成功的 JSON 响应

## 📄 页面说明

### index.html
- 项目首页
- 展示功能介绍
- 包含快速开始指南
- 链接到登录页面和 API 文档

### login.html
- OAuth2 登录页面
- 点击按钮自动跳转到 Second Me 授权
- 显示使用说明
- 响应式设计，支持移动端

## 🔧 配置说明

环境变量中配置：
```
SECOND_ME_REDIRECT_URI=http://localhost:8000/auth/callback
```

这个地址是 Second Me 授权后回调的地址。

## 📚 API 文档

访问 Swagger UI：http://localhost:8000/docs
