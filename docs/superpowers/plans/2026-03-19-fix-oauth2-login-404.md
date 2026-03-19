# 修复 OAuth2 登录 404 错误实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复访问 `http://localhost:8000/api/v1/auth/oauth2/login` 时出现 404 Not Found 错误的问题，确保 OAuth2 登录路由正常工作。

**Architecture:** 问题是 FastAPI 路由前缀配置不一致。`auth.py` 中的路由器没有设置 `prefix="/auth"`，导致注册到 `main.py` 时只有 `/api/v1` 前缀。解决方案是在 `auth.py` 中添加 `prefix="/auth"`。

**Tech Stack:** Python, FastAPI, Router Configuration

---

## 问题诊断

### 当前状态
```
实际路由: /api/v1/oauth2/login ✅ 存在
期望路由: /api/v1/auth/oauth2/login ❌ 不存在
```

### 路由配置对比

**app/main.py:80**
```python
app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
```

**app/api/v1/auth.py:23**
```python
router = APIRouter(tags=["Auth"])
# ❌ 缺少 prefix="/auth"
```

**结果：** `/api/v1` + `/oauth2/login` = `/api/v1/oauth2/login`

**期望：** `/api/v1` + `/auth` + `/oauth2/login` = `/api/v1/auth/oauth2/login`

---

## 修复方案

### 方案选择

有两个可行的修复方案：

1. **方案 A（推荐）：修改 `auth.py` 添加 `prefix="/auth"`**
   - 优点：符合项目文档约定，保持一致性
   - 影响：前端需要保持 `/api/v1/auth/oauth2/login` 路径

2. **方案 B：修改所有前端代码使用 `/api/v1/oauth2/login`**
   - 优点：后端改动最小
   - 缺点：需要修改多处前端代码，违反文档规范

**选择方案 A**，因为：
- 符合 `CLAUDE.md` 文档规范
- 保持项目架构一致性
- 前端已经使用了正确的路径

---

## 实施计划

### 任务 1: 修改 auth.py 路由器配置

**文件:**
- 修改: `D:\SocialClaw\app\api\v1\auth.py:23`

- [ ] **步骤 1: 修改路由器定义，添加 prefix**

```python
router = APIRouter(prefix="/auth", tags=["Auth"])
```

- [ ] **步骤 2: 验证路由路径正确性**

修改后，路由映射应为：
```
/api/v1 (from main.py) + /auth (from auth.py prefix) + /oauth2/login (endpoint)
= /api/v1/auth/oauth2/login ✅
```

- [ ] **步骤 3: 检查所有端点是否兼容**

确认 `auth.py` 中的所有端点都不需要修改（因为 prefix 会自动添加）：
- ✅ `/oauth2/login` → `/auth/oauth2/login`
- ✅ `/callback` → `/auth/callback`
- ✅ `/refresh` → `/auth/refresh`

- [ ] **步骤 4: 提交更改**

```bash
git add app/api/v1/auth.py
git commit -m "fix(auth): 添加 auth 路由器 prefix 确保路由一致性"
```

### 任务 2: 验证路由注册正确

**文件:**
- 无需修改文件，仅需验证

- [ ] **步骤 1: 启动开发服务器**

```bash
cd D:\SocialClaw
poetry run uvicorn app.main:app --reload
```

- [ ] **步骤 2: 检查 FastAPI 文档**

访问：`http://localhost:8000/docs`

期望：可以看到 `/api/v1/auth/oauth2/login` 路由

- [ ] **步骤 3: 检查路由列表**

访问：`http://localhost:8000/openapi.json`

在文档中搜索 `oauth2/login`，应该找到：
```json
"/api/v1/auth/oauth2/login": {
  "get": {
    "summary": "Oauth2 Login",
    ...
  }
}
```

- [ ] **步骤 4: 手动测试路由**

```bash
curl -v http://localhost:8000/api/v1/auth/oauth2/login
```

期望输出：
```
HTTP/1.1 307 Temporary Redirect
Location: https://go.second.me/oauth/?client_id=xxx&...
```

- [ ] **步骤 5: 验证旧路径不再存在**

```bash
curl -v http://localhost:8000/api/v1/oauth2/login
```

期望输出：
```
HTTP/1.1 404 Not Found
```

- [ ] **步骤 6: 提交验证结果**

```bash
# 记录验证结果到日志
echo "✅ /api/v1/auth/oauth2/login 路由验证通过" >> docs/fixes/oauth2-login-fix.log
```

### 任务 3: 更新相关测试

**文件:**
- 修改: `D:\SocialClaw\tests\test_auth_oauth2.py`
- 修改: `D:\SocialClaw\tests\test_auth_integration.py`

- [ ] **步骤 1: 更新 test_auth_oauth2.py 中的测试路径**

查找并替换：
```python
# 修改前
response = client.get("/api/v1/oauth2/login")

# 修改后
response = client.get("/api/v1/auth/oauth2/login")
```

影响的测试：
- [ ] `test_oauth2_login_redirect` - 第 24 行
- [ ] `test_oauth2_callback` - 第 66 行（如果存在）

- [ ] **步骤 2: 更新 test_auth_integration.py 中的测试路径**

查找并替换：
```python
# 修改前
response = client.get("/api/v1/oauth2/login")

# 修改后
response = client.get("/api/v1/auth/oauth2/login")
```

影响的测试：
- [ ] 所有涉及 oauth2/login 的测试

- [ ] **步骤 3: 运行测试验证**

```bash
cd D:\SocialClaw
poetry run pytest tests/test_auth_oauth2.py -v
poetry run pytest tests/test_auth_integration.py -v
```

期望输出：
```
✅ All tests passed
```

- [ ] **步骤 4: 提交测试更新**

```bash
git add tests/test_auth_oauth2.py tests/test_auth_integration.py
git commit -m "test(auth): 更新 OAuth2 测试路径以匹配新路由"
```

### 任务 4: 更新文档（可选，仅当必要时）

**文件:**
- 查看: `D:\SocialClaw\frontend\FIXED.md`
- 查看: `D:\SocialClaw\docs\superpowers\plans\2026-03-18-fix-oauth2-login-not-found.md`

- [ ] **步骤 1: 检查 frontend/FIXED.md 是否需要更新**

如果文档中描述了临时解决方案（使用 `/api/v1/oauth2/login`），需要更新为正确路径。

- [ ] **步骤 2: 检查历史计划文档是否需要注释**

在 `2026-03-18-fix-oauth2-login-not-found.md` 末尾添加注释：
```markdown
## 更新说明

此计划已被 2026-03-19 修复。当前正确的路由路径为：
- ✅ `/api/v1/auth/oauth2/login` - OAuth2 授权登录
- ✅ `/api/v1/auth/callback` - OAuth2 回调处理
- ✅ `/api/v1/auth/refresh` - Token 刷新
```

- [ ] **步骤 3: 提交文档更新（如有）**

```bash
git add frontend/FIXED.md docs/superpowers/plans/2026-03-18-fix-oauth2-login-not-found.md
git commit -m "docs: 更新 OAuth2 路由文档"
```

---

## 验收标准

### 功能测试
- [ ] 访问 `http://localhost:8000/api/v1/auth/oauth2/login` 返回 307 重定向到 Second Me
- [ ] 访问 `http://localhost:8000/api/v1/auth/callback` 返回 400（缺少 code 参数，但路由存在）
- [ ] 访问 `http://localhost:8000/api/v1/auth/refresh` 需要认证（但路由存在）
- [ ] 访问 `http://localhost:8000/api/v1/oauth2/login` 返回 404 Not Found

### API 文档
- [ ] FastAPI 文档 (`/docs`) 显示 `/api/v1/auth/oauth2/login` 路由
- [ ] OpenAPI 规范 (`/openapi.json`) 包含正确的路由定义

### 测试
- [ ] 所有 OAuth2 相关测试通过
- [ ] 所有集成测试通过

### 前端集成
- [ ] 前端代码中的 `API_BASE_URL` 配置正确
- [ ] 前端调用路径为 `/api/v1/auth/oauth2/login`

---

## 所需文件修改清单

| 文件路径 | 操作 | 说明 |
|---------|------|------|
| `app/api/v1/auth.py` | 修改 | 添加 `prefix="/auth"` 到路由器定义 |
| `tests/test_auth_oauth2.py` | 修改 | 更新测试路径为 `/api/v1/auth/oauth2/login` |
| `tests/test_auth_integration.py` | 修改 | 更新测试路径为 `/api/v1/auth/oauth2/login` |
| `frontend/FIXED.md` | 查看 | 确认是否需要更新临时解决方案说明 |
| `docs/superpowers/plans/2026-03-18-fix-oauth2-login-not-found.md` | 查看 | 添加更新说明 |

---

## 风险评估

### 高风险
- ❌ 无

### 中风险
- ⚠️ 如果有其他地方硬编码了 `/api/v1/oauth2/login` 路径，需要一并修改

### 低风险
- ✅ 测试已覆盖主要路径
- ✅ 前端代码已经使用了正确的路径
- ✅ 修改范围小，影响可控

---

## 回滚方案

如果修复导致问题，可以快速回滚：

```bash
# 回滚 auth.py 的修改
git checkout HEAD app/api/v1/auth.py

# 回滚测试文件的修改
git checkout HEAD tests/test_auth_oauth2.py
git checkout HEAD tests/test_auth_integration.py
```

然后重启服务器验证回滚成功。

---

## 完成检查清单

修复完成后，请确认：

- [ ] 后端路由 `/api/v1/auth/oauth2/login` 正常工作
- [ ] 所有相关测试通过
- [ ] FastAPI 文档显示正确路由
- [ ] 前端代码使用正确路径
- [ ] 无其他地方使用旧路径 `/api/v1/oauth2/login`
- [ ] 文档已更新（如有需要）

---

**计划制定者:** AI Assistant
**计划日期:** 2026-03-19
**预计完成时间:** 10-15 分钟
