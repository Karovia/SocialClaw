# OAuth2 404 Not Found 修复计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复访问 `http://localhost:8000/auth/oauth2/login` 时出现 404 Not Found 错误的问题

**Architecture:**
- 问题原因：FastAPI 路由器配置了双重前缀（double prefix），auth router 在 `auth.py` 中定义了 `prefix="/auth"`，在 `main.py` 中又添加了 `prefix="/api/v1"`，导致最终路由变成 `/api/v1/auth/auth/oauth2/login` 而不是 `/api/v1/auth/oauth2/login`
- 解决方案：移除 `auth.py` 中的 `prefix="/auth"`，保持 `main.py` 中的 `prefix="/api/v1"`，这样路由就是 `/api/v1/auth/oauth2/login`

**Tech Stack:** FastAPI, Python

---

## 问题诊断

访问 `http://localhost:8000/auth/oauth2/login` 返回 `{"detail":"Not Found"}`，正确路径应该是 `http://localhost:8000/api/v1/auth/oauth2/login`。

### 当前路由配置

**`app/api/v1/auth.py` 第 20 行：**
```python
router = APIRouter(tags=["Auth"])
```

**`app/main.py` 第 67 行：**
```python
app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
```

这意味着：
- ✅ 实际路由：`/api/v1/oauth2/login`
- ✅ 实际路由：`/api/v1/callback`
- ❌ 访问 `/auth/oauth2/login` 不存在
- ❌ 访问 `/api/v1/auth/oauth2/login` 不存在（因为 auth.py 没有 prefix）

### 前端配置问题

**`frontend/src/api/auth.ts` 第 64-69 行：**
```typescript
export const oauth2Login = (): void => {
  const loginUrl = `${API_BASE_URL.replace('/api/v1', '')}/auth/oauth2/login`;
  window.location.href = loginUrl;
};
```

这个构造会生成：`http://localhost:8000/auth/oauth2/login`（缺少 `/api/v1`）

---

### Task 1: 修复前端 OAuth2 登录端点路径

**Files:**
- Modify: `D:\SocialClaw\frontend\src\api\auth.ts:64-69`

- [ ] **Step 1: 修改 oauth2Login 函数的 URL 构造逻辑**

```typescript
/**
 * OAuth2 登录 - 跳转到后端 OAuth2 登录端点
 */
export const oauth2Login = (): void => {
  // 跳转到后端的 OAuth2 登录端点
  // 后端会重定向到 Second Me 授权，然后回调处理，最后重定向回前端
  const loginUrl = `${API_BASE_URL.replace('/api/v1', '')}/api/v1/auth/oauth2/login`;
  window.location.href = loginUrl;
};
```

- [ ] **Step 2: 保存文件并测试编译**

运行：检查 TypeScript 编译错误
```bash
cd frontend
npm run build
```

期望：编译成功，无错误

- [ ] **Step 3: 重启前端开发服务器**

```bash
cd frontend
npm run dev
```

- [ ] **Step 4: 提交更改**

```bash
git add frontend/src/api/auth.ts
git commit -m "fix(auth): 修复 OAuth2 登录端点路径，添加 /api/v1 前缀"
```

---

### Task 2: 验证后端路由配置正确

**Files:**
- Verify: `D:\SocialClaw\app\api\v1\auth.py:20`
- Verify: `D:\SocialClaw\app\main.py:67`

- [ ] **Step 1: 确认 auth.py 中的 router 定义**

检查 `app/api/v1/auth.py` 第 20 行应该是：
```python
router = APIRouter(tags=["Auth"])
```

确保没有 `prefix="/auth"`！

- [ ] **Step 2: 确认 main.py 中的路由注册**

检查 `app/main.py` 第 67 行应该是：
```python
app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
```

- [ ] **Step 3: 查看 FastAPI 自动生成的 OpenAPI 文档**

访问：`http://localhost:8000/docs`

期望看到的路由：
- `GET /api/v1/auth/oauth2/login`
- `GET /api/v1/auth/callback`
- `POST /api/v1/auth/refresh`

- [ ] **Step 4: 提交验证结果（如果发现问题则修复）**

如果发现 `auth.py` 还有 `prefix="/auth"`，立即修复并提交：
```python
# ❌ 错误
router = APIRouter(prefix="/auth", tags=["Auth"])

# ✅ 正确
router = APIRouter(tags=["Auth"])
```

---

### Task 3: 重启后端服务并测试完整流程

**Files:**
- None (运行时验证)

- [ ] **Step 1: 停止当前运行的后端服务**

找到后端进程并停止（如果使用终端，按 Ctrl+C）

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

- [ ] **Step 3: 验证后端路由已正确注册**

访问：`http://localhost:8000/docs`

确认可以看到 `/api/v1/auth/oauth2/login` 路由

- [ ] **Step 4: 测试 OAuth2 登录端点**

在浏览器中访问：`http://localhost:3000/login`

点击"使用 Second Me 登录"按钮

期望行为：
1. 跳转到 `http://localhost:8000/api/v1/auth/oauth2/login`
2. 立即重定向到 Second Me 授权页面
3. 在 Second Me 授权后，回调到 `http://localhost:8000/api/v1/auth/callback?code=xxx`
4. 后端处理后重定向回前端：`http://localhost:3000/login?access_token=xxx&user_id=xxx...`
5. 前端自动保存 token 和 user_info 到 localStorage
6. 自动重定向到 `/dashboard`
7. 左侧边栏显示用户名和头像

- [ ] **Step 5: 检查浏览器控制台和网络请求**

打开浏览器开发者工具（F12），查看：
- Network 标签：确认请求路径是 `/api/v1/auth/oauth2/login`
- Console 标签：确认没有错误
- Application → Local Storage：确认有 `access_token` 和 `user_info`

- [ ] **Step 6: 记录测试结果**

如果测试成功：在计划中标记此任务完成
如果测试失败：记录错误信息，继续下一步诊断

---

### Task 4: 诊断和修复（如果测试失败）

**Files:**
- Read: `D:\SocialClaw\app\api\v1\auth.py`
- Read: `D:\SocialClaw\frontend\src\api\auth.ts`
- Read: `D:\SocialClaw\frontend\src\pages\Login.tsx`

- [ ] **Step 1: 检查后端日志**

查看后端终端输出，确认：
- 是否有请求到达 `/api/v1/auth/oauth2/login`
- 是否正确重定向到 Second Me
- 回调处理是否成功
- 是否正确重定向回前端

- [ ] **Step 2: 检查路由注册顺序**

确保 `main.py` 中 auth_router 是第一个注册的：
```python
app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
```

- [ ] **Step 3: 如果还是 404，检查是否有多余的中间件或异常处理器**

查看 `app/main.py` 是否有自定义的 404 处理器或其他可能拦截路由的代码

- [ ] **Step 4: 验证 URL 构造逻辑**

在 `frontend/src/api/auth.ts` 中添加调试日志：
```typescript
export const oauth2Login = (): void => {
  const loginUrl = `${API_BASE_URL.replace('/api/v1', '')}/api/v1/auth/oauth2/login`;
  console.log('OAuth2 login URL:', loginUrl);
  window.location.href = loginUrl;
};
```

- [ ] **Step 5: 提交修复（如果有）**

```bash
git add -A
git commit -m "fix: 诊断并修复 OAuth2 404 问题"
```

---

## 验收标准

✅ 访问 `http://localhost:3000/login` 点击登录按钮后，正确跳转到 Second Me 授权页面
✅ 授权完成后，成功重定向回前端并显示用户信息
✅ 用户信息（username、avatar）正确显示在左侧边栏
✅ 控制台无错误，网络请求正常
✅ 后端日志显示完整的 OAuth2 流程处理成功
