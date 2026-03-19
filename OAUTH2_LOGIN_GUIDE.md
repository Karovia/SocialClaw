# OAuth2 登录正确流程

## ✅ 正确的测试步骤

### 1. 启动后端服务
```bash
cd D:/Socialclaw
poetry run uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. 启动前端服务
```bash
cd D:/Socialclaw/frontend
npm run dev
```

### 3. 访问前端登录页
```
http://localhost:3000/login
```

### 4. 点击"使用 Second Me 登录"按钮

系统会自动完成以下流程：

```
┌─────────────────────────────────────────────────────────┐
│ 1. 前端调用后端 OAuth2 登录端点                          │
│    http://localhost:8000/api/v1/auth/oauth2/login        │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ 2. 后端生成授权 URL 并重定向到 Second Me                 │
│    https://go.second.me/oauth/                           │
│      ?client_id=29347211-adcf-46aa-b135-128645948227    │
│      &redirect_uri=http://localhost:8000/api/v1/auth/callback │
│      &response_type=code                                 │
│      &scope=user.info,user.info.shades,user.info.softmemory │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ 3. 用户在 Second Me 授权页面点击"授权"                   │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ 4. Second Me 重定向回调到后端                             │
│    http://localhost:8000/api/v1/auth/callback?code=xxx   │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ 5. 后端处理回调：                                         │
│    - 用 code 换取 access_token                           │
│    - 获取用户信息                                        │
│    - 创建/获取 SocialClaw 用户账号                       │
│    - 生成 JWT Token                                      │
│    - 重定向回前端                                        │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ 6. 前端接收 Token 并保存到 localStorage                   │
│    跳转到 /my-agents 页                                   │
└─────────────────────────────────────────────────────────┘
```

## 🔑 Second Me 后台配置

### 必须配置的重定向 URI：
```
http://localhost:8000/api/v1/auth/callback
```

### ❌ 不要配置的错误 URI：
- `http://localhost:8080/api/v1/auth/callback` （端口错误）
- `http://localhost:3000/api/auth/callback` （端口和路径错误）
- `https://socialclaw.com/auth/callback` （未部署前不要用）

## 🚫 不要做的事情

1. **不要手动构造授权 URL** - 让后端自动生成
2. **不要直接访问 Second Me 的 OAuth URL** - 通过前端登录按钮
3. **不要使用错误的端口（8080、3000）** - 后端端口必须是 8000
4. **不要在后台配置多个不同的 redirect_uri** - 只配置一个正确的

## 🔍 验证配置

### 检查后端配置
```bash
cd D:/Socialclaw
poetry run python -c "from app.core.config import settings; print('Redirect URI:', settings.SECOND_ME_REDIRECT_URI)"
# 应该输出：http://localhost:8000/api/v1/auth/callback
```

### 检查前端配置
```bash
cat D:/Socialclaw/frontend/.env | grep VITE_OAUTH_REDIRECT_URI
# 应该输出：VITE_OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback
```

## 🐛 如果仍然报错

### 检查 Second Me 后台配置
1. 登录 [Second Me 开发者平台](https://go.second.me/developer)
2. 找到应用（App ID: `29347211-adcf-46aa-b135-128645948227`）
3. 检查"重定向 URI"是否为：`http://localhost:8000/api/v1/auth/callback`
4. 删除其他错误的 URI
5. 保存配置

### 检查后端是否运行
```bash
curl http://localhost:8000/api/v1/auth/oauth2/login -I
# 应该返回 302 Redirect
```

### 检查前端是否运行
```bash
curl http://localhost:3000/login -I
# 应该返回 200 OK
```

## ✅ 成功标志

登录成功后：
- 前端会跳转到 `/my-agents` 页
- `localStorage` 中会有 `access_token` 和 `user_info`
- 可以访问需要认证的 API
