# OAuth2 回调 404 Not Found 修复计划

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复访问 `/api/v1/auth/callback` 时出现 404 Not Found 的问题

**Architecture:**
- 问题原因：Second Me 应用配置中的 Redirect URI 包含了错误的路径 `/api/v1/auth/callback`，而后端实际路由是 `/api/v1/callback`
- 根本原因：环境变量 `.env` 中的 `SECOND_ME_REDIRECT_URI` 配置错误，且 Second Me 开发者后台的应用配置也需要同步修改

**Tech Stack:** FastAPI, Python, Second Me OAuth2

---

## 问题诊断

### 当前错误配置

**`.env` 文件配置：**
```env
SECOND_ME_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback  ❌ 错误
```

**Second Me 应用后台配置：**
```
Redirect URI: http://localhost:8000/api/v1/auth/callback  ❌ 错误
```

**后端实际路由：**
```python
@router.get("/callback")
async def oauth2_callback(code: str):
    ...
```

通过 `main.py` 注册时添加了 `/api/v1` 前缀：
```python
app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
```

所以最终路由是：`GET /api/v1/callback` ✅

### OAuth2 流程中出现的问题

```
1. 用户点击登录 → 后端重定向到 Second Me
   Location: https://go.second.me/oauth/?client_id=xxx&redirect_uri=http://localhost:8000/api/v1/auth/callback&...

2. 用户授权 → Second Me 回调到 redirect_uri
   GET http://localhost:8000/api/v1/auth/callback?code=xxx  ❌ 404 Not Found

3. 错误原因：后端没有 /api/v1/auth/callback 路由
```

---

### Task 1: 修改本地环境变量配置

**Files:**
- Modify: `D:\SocialClaw\.env`

- [ ] **Step 1: 修改 SECOND_ME_REDIRECT_URI**

打开 `.env` 文件，找到并修改：

```env
# 修改前 ❌
SECOND_ME_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback

# 修改后 ✅
SECOND_ME_REDIRECT_URI=http://localhost:8000/api/v1/callback
```

确保有两个地方都修改（第 3 行和第 18 行附近）

- [ ] **Step 2: 验证环境变量**

运行命令验证修改是否生效：

```bash
poetry run python -c "from app.core.config import settings; print('Redirect URI:', settings.SECOND_ME_REDIRECT_URI)"
```

期望输出：
```
Redirect URI: http://localhost:8000/api/v1/callback
```

- [ ] **Step 3: 提交更改**

```bash
git add .env
git commit -m "fix(auth): 修复 Second Me Redirect URI 路径，移除多余的 /auth"
```

---

### Task 2: 修改 Second Me 开发者后台配置

**Files:**
- None (Second Me 后台配置)

- [ ] **Step 1: 登录 Second Me 开发者平台**

访问：https://develop.second.me/

使用您的开发者账号登录

- [ ] **Step 2: 找到 SocialClaw 应用**

1. 进入 "我的应用" 或 "应用管理"
2. 找到应用：`SocialClaw` 或 App ID: `29347211-adcf-46aa-b135-128645948227`
3. 点击"编辑"或"配置"

- [ ] **Step 3: 修改 Redirect URI**

找到 "回调地址" 或 "Redirect URI" 配置项：

```
修改前 ❌
http://localhost:8000/api/v1/auth/callback

修改后 ✅
http://localhost:8000/api/v1/callback
```

**注意：**
- 如果有多个 Redirect URI（开发、测试、生产），需要全部修改
- 确保修改后点击"保存"

- [ ] **Step 4: 验证配置**

在 Second Me 应用详情页，确认 Redirect URI 已更新为：
```
http://localhost:8000/api/v1/callback
```

---

### Task 3: 重启后端服务

**Files:**
- None (运行时操作)

- [ ] **Step 1: 停止当前后端服务**

找到运行 uvicorn 的终端，按 `Ctrl+C` 停止

或者使用命令：
```bash
taskkill /F /IM uvicorn.exe
```

- [ ] **Step 2: 重启后端服务**

```bash
cd D:\SocialClaw
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

期望输出：
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Started reloader process
INFO:     Started server process
```

- [ ] **Step 3: 验证环境变量已加载**

查看后端启动日志，确认读取了正确的 Redirect URI

或者在代码中添加调试日志：
```python
print(f"✓ Second Me Redirect URI: {settings.SECOND_ME_REDIRECT_URI}")
```

---

### Task 4: 测试 OAuth2 完整流程

**Files:**
- None (运行时验证)

- [ ] **Step 1: 确认前端已启动**

```bash
cd frontend
npm run dev
```

访问：`http://localhost:3000/login`

- [ ] **Step 2: 点击登录按钮**

点击"使用 Second Me 登录"按钮

- [ ] **Step 3: 验证重定向到 Second Me**

浏览器地址栏应该变为：
```
https://go.second.me/oauth/?client_id=29347211-adcf-46aa-b135-128645948227&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fapi%2Fv1%2Fcallback&response_type=code&scope=user.info%2Cuser.info.shades%2Cuser.info.softmemory
```

**关键验证：** `redirect_uri` 参数应该是 `http://localhost:8000/api/v1/callback`（没有 `/auth`）

- [ ] **Step 4: 在 Second Me 授权**

1. 在 Second Me 授权页面，确认回调地址显示正确
2. 点击"授权"按钮

- [ ] **Step 5: 验证回调处理**

Second Me 授权后，应该回调到：
```
http://localhost:8000/api/v1/callback?code=lba_ac_xxx
```

**关键验证：** 路径是 `/api/v1/callback`（没有 `/auth`），应该不再出现 404 错误

- [ ] **Step 6: 验证后端处理回调**

查看后端终端输出，应该看到：
```
✓ OAuth2 callback successful for user soc_user_xxx
✓ Redirecting to: http://localhost:3000/login?access_token=xxx&user_id=xxx...
```

- [ ] **Step 7: 验证前端接收 Token**

浏览器应该重定向到：
```
http://localhost:3000/login?access_token=xxx&user_id=xxx&username=xxx...
```

前端应该：
1. 读取 URL 参数
2. 保存 `access_token` 到 localStorage
3. 保存 `user_info` 到 localStorage
4. 重定向到 `/dashboard`

- [ ] **Step 8: 验证登录成功**

访问 `http://localhost:3000/dashboard`

左侧边栏应该显示：
- 用户名
- 头像（或首字母）

---

### Task 5: 验证和记录

**Files:**
- None (验证操作)

- [ ] **Step 1: 检查浏览器控制台**

打开开发者工具（F12），查看 Console 标签：
- 确认无错误
- 可以看到保存 token 的日志

- [ ] **Step 2: 检查 Local Storage**

Application → Local Storage → http://localhost:3000

确认存在：
- `access_token`: JWT token
- `user_info`: JSON 格式的用户信息

- [ ] **Step 3: 检查网络请求**

Network 标签：
- 确认 OAuth2 登录请求路径正确
- 确认回调请求返回 307 或 302 重定向（不是 404）

- [ ] **Step 4: 检查后端日志**

后端终端应该显示完整的 OAuth2 流程：
```
INFO:     127.0.0.1:xxxxx - "GET /api/v1/oauth2/login HTTP/1.1" 307
INFO:     127.0.0.1:xxxxx - "GET /api/v1/callback?code=xxx HTTP/1.1" 302
✓ OAuth2 callback successful for user soc_user_xxx
✓ Redirecting to: http://localhost:3000/login?access_token=...
```

- [ ] **Step 5: 记录测试结果**

如果测试成功：
- 标记所有任务为完成
- 在文档中记录成功

如果测试失败：
- 记录具体错误信息
- 检查 Second Me 后台配置是否正确保存
- 检查后端服务是否重启成功
- 检查环境变量是否正确加载

---

## 重要注意事项

### ⚠️ Second Me 后台配置必须修改

仅仅修改本地 `.env` 文件是不够的！Second Me 会严格校验 `redirect_uri` 参数，如果与后台配置不一致，会拒绝授权。

### 📋 完整的修复清单

1. ✅ 修改 `.env` 文件中的 `SECOND_ME_REDIRECT_URI`
2. ⚠️ **修改 Second Me 开发者后台的应用配置**
3. ✅ 重启后端服务
4. ⚠️ **重新进行 OAuth2 授权测试**

### 🔍 调试技巧

如果还是出现 404，可以：

1. **检查 Second Me 构造的回调 URL**

   在 Second Me 授权页面，右键 → "检查" → 查看 Network 标签，找到重定向请求，确认 URL 是否正确。

2. **手动测试回调路由**

   ```bash
   curl -v "http://localhost:8000/api/v1/callback?code=test"
   ```

   应该返回 400（code 无效），而不是 404。

3. **查看后端路由列表**

   ```bash
   curl http://localhost:8000/openapi.json | grep "callback"
   ```

   应该看到 `/api/v1/callback` 路由。

---

## 验收标准

✅ `.env` 文件中的 `SECOND_ME_REDIRECT_URI` 已修改为 `http://localhost:8000/api/v1/callback`
✅ Second Me 开发者后台的 Redirect URI 已同步修改
✅ 后端服务已重启，环境变量已加载
✅ 访问 `/api/v1/callback?code=xxx` 不再返回 404
✅ 完整的 OAuth2 授权流程正常工作
✅ 用户登录成功后可以访问受保护的页面
