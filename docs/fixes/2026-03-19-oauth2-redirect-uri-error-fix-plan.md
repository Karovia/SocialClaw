# OAuth2 回调地址错误问题修复方案

**创建日期**: 2026-03-19
**问题状态**: 待修复
**影响范围**: 登录功能无法使用

---

## 问题描述

用户登录后显示 **"回调地址错误"** (Redirect URI mismatch)，导致无法完成 OAuth2 授权流程。

### 症状

1. 点击"使用 Second Me 登录"按钮
2. 跳转到 Second Me 授权页面
3. 授权后显示错误提示：**"回调地址不匹配"**
4. 无法完成登录流程

---

## 根本原因分析

### 配置状态检查（2026-03-19）

| 配置文件 | 当前值 | 状态 |
|----------|--------|------|
| `app/core/config.py` (默认值) | `http://localhost:8000/api/v1/auth/callback` | ✅ 正确 |
| `.env` 文件 | `http://localhost:8000/api/v1/auth/callback` | ✅ 正确 |
| `frontend/.env` | `http://localhost:8000/api/v1/auth/callback` | ✅ 正确 |
| `frontend/src/api/auth.ts` (默认值) | `http://localhost:3000/auth/callback` | ❌ **错误** |

### 问题定位

**核心问题**：前端代码中的默认回调地址与实际配置不一致。

```typescript
// frontend/src/api/auth.ts:6
const OAUTH_REDIRECT_URI = import.meta.env.VITE_OAUTH_REDIRECT_URI || 'http://localhost:3000/auth/callback';
```

**问题点**：
- 默认值是 `http://localhost:3000/auth/callback`（前端 3000 端口）
- 但实际应该使用后端 8000 端口：`http://localhost:8000/api/v1/auth/callback`

**为什么配置文件正确但仍报错？**

1. **前端 .env 文件未生效**：Vite 需要重新启动才能读取新的环境变量
2. **浏览器缓存**：旧的构建文件可能还在缓存中
3. **Second Me 后台配置**：需要确认 Second Me 开发者平台中的回调地址是否正确

---

## 修复方案

### 方案 1：检查并重启前端服务（推荐）

#### 步骤 1：确认前端 .env 配置

检查 `frontend/.env` 文件：

```bash
cat D:/Socialclaw/frontend/.env
```

**期望输出**：
```
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_SECOND_ME_CLIENT_ID=29347211-adcf-46aa-b135-128645948227
VITE_OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback
```

#### 步骤 2：清除前端缓存并重启

```bash
# 进入前端目录
cd D:/Socialclaw/frontend

# 清除 Vite 缓存
rm -rf node_modules/.vite

# 重启开发服务器
npm run dev
```

#### 步骤 3：清除浏览器缓存

1. **Chrome/Edge**: `Ctrl + Shift + Delete` → 清除缓存和 Cookie
2. **或使用无痕模式**：`Ctrl + Shift + N` 打开无痕窗口测试

---

### 方案 2：检查 Second Me 后台配置

#### 步骤 1：登录 Second Me 开发者平台

访问：[https://second-me.cn](https://second-me.cn) 或 [https://develop.second.me](https://develop.second.me)

#### 步骤 2：检查应用回调地址配置

1. 进入"开发者中心"
2. 找到应用：**SocialClaw**（App ID: `29347211-adcf-46aa-b135-128645948227`）
3. 检查"回调地址"或"Redirect URI"配置

**必须包含以下地址**：
```
http://localhost:8000/api/v1/auth/callback
```

#### 步骤 3：如果不存在，添加回调地址

1. 点击"编辑应用"
2. 在"回调地址"字段添加：
   ```
   http://localhost:8000/api/v1/auth/callback
   ```
3. 保存配置

---

### 方案 3：调试和验证

#### 步骤 1：验证后端配置

在后端启动时添加调试输出：

```python
# app/main.py
from app.core.config import settings

# 在 app = FastAPI(...) 之前添加
print("=" * 60)
print("OAuth2 配置检查:")
print(f"CLIENT_ID: {settings.SECOND_ME_CLIENT_ID}")
print(f"REDIRECT_URI: {settings.SECOND_ME_REDIRECT_URI}")
print(f"OAUTH_URL: {settings.SECOND_ME_OAUTH_URL}")
print("=" * 60)
```

重启后端服务，确认输出正确：

```bash
cd D:/Socialclaw
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**期望输出**：
```
============================================================
OAuth2 配置检查:
CLIENT_ID: 29347211-adcf-46aa-b135-128645948227
REDIRECT_URI: http://localhost:8000/api/v1/auth/callback
OAUTH_URL: https://go.second.me/oauth/
============================================================
```

#### 步骤 2：验证前端配置

在浏览器控制台检查环境变量：

1. 打开前端页面：`http://localhost:3000`
2. 打开浏览器控制台（F12）
3. 执行：

```javascript
console.log("OAuth Redirect URI:", import.meta.env.VITE_OAUTH_REDIRECT_URI)
```

**期望输出**：
```
OAuth Redirect URI: http://localhost:8000/api/v1/auth/callback
```

#### 步骤 3：手动测试授权流程

访问授权页面：

```
https://go.second.me/oauth/?
  client_id=29347211-adcf-46aa-b135-128645948227&
  redirect_uri=http://localhost:8000/api/v1/auth/callback&
  response_type=code&
  scope=user.info,user.info.shades,user.info.softmemory
```

**注意**：确保 `redirect_uri` 是 `http://localhost:8000/api/v1/auth/callback`

---

## 完整修复流程

### 第一步：检查所有配置文件

```bash
# 检查后端配置
cat D:/Socialclaw/.env | grep REDIRECT
cat D:/Socialclaw/app/core/config.py | grep SECOND_ME_REDIRECT_URI

# 检查前端配置
cat D:/Socialclaw/frontend/.env | grep VITE_OAUTH_REDIRECT_URI
cat D:/Socialclaw/frontend/src/api/auth.ts | grep OAUTH_REDIRECT_URI
```

### 第二步：确认 Second Me 后台配置

1. 登录 Second Me 开发者平台
2. 检查应用回调地址是否包含：`http://localhost:8000/api/v1/auth/callback`
3. 如果不存在，添加并保存

### 第三步：重启服务

```bash
# 1. 停止所有服务（Ctrl + C）

# 2. 清除缓存
cd D:/Socialclaw/frontend
rm -rf node_modules/.vite
cd ..

# 3. 启动后端
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. 启动前端（新终端）
cd D:/Socialclaw/frontend
npm run dev
```

### 第四步：清除浏览器缓存并测试

1. 清除浏览器缓存（Ctrl + Shift + Delete）
2. 或使用无痕模式测试
3. 访问：`http://localhost:3000`
4. 点击"使用 Second Me 登录"
5. 在 Second Me 页面点击"授权"
6. 应该成功回调到前端并显示登录成功

---

## 验证检查清单

完成修复后，请确认以下所有项目都通过：

- [ ] 后端 `.env` 中 `SECOND_ME_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback`
- [ ] 前端 `frontend/.env` 中 `VITE_OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback`
- [ ] Second Me 后台应用配置包含回调地址 `http://localhost:8000/api/v1/auth/callback`
- [ ] 后端服务运行在 8000 端口
- [ ] 前端服务运行在 3000 端口
- [ ] 前端控制台输出的 `VITE_OAUTH_REDIRECT_URI` 正确
- [ ] 后端启动日志显示的 `REDIRECT_URI` 正确
- [ ] 浏览器缓存已清除
- [ ] 授权成功后能够正确回调到前端

---

## 常见问题

### Q1: 修改 .env 后仍报错

**解决**：
1. 确认服务已重启
2. 清除前端构建缓存：`rm -rf node_modules/.vite`
3. 清除浏览器缓存
4. 检查 Second Me 后台配置

### Q2: 授权后跳转到错误地址

**原因**：前端代码中硬编码的默认值未被覆盖

**解决**：
1. 确认 `frontend/.env` 文件存在且配置正确
2. 重启前端服务
3. 检查浏览器控制台的环境变量输出

### Q3: Second Me 后台无法添加回调地址

**解决**：
1. 确认登录的是正确的开发者账号
2. 检查应用是否已经创建
3. 如果应用未创建，需要先创建应用并获取 App ID 和 Secret

### Q4: 本地开发和生产环境的回调地址不同

**配置**：

开发环境（`.env` 和 `frontend/.env`）：
```env
SECOND_ME_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback
VITE_OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback
```

生产环境（Second Me 后台）：
```env
https://socialclaw.com/api/v1/auth/callback
```

在 Second Me 后台添加多个回调地址：
```
http://localhost:8000/api/v1/auth/callback
http://test.socialclaw.com/api/v1/auth/callback
https://socialclaw.com/api/v1/auth/callback
```

---

## 技术细节

### OAuth2 授权流程中的回调地址

```
用户点击登录
    ↓
前端构造授权 URL:
https://go.second.me/oauth/?
  client_id=29347211-adcf-46aa-b135-128645948227
  &redirect_uri=http://localhost:8000/api/v1/auth/callback  ← 必须匹配
  &response_type=code
  &scope=user.info,user.info.shades,user.info.softmemory
    ↓
Second Me 授权页面
    ↓
用户点击"授权"
    ↓
Second Me 回调:
http://localhost:8000/api/v1/auth/callback?code=AUTH_CODE
    ↓
后端处理回调:
1. 用 code 换取 access_token
2. 获取用户信息
3. 创建/更新用户账号
4. 生成 JWT Token
    ↓
重定向到前端:
http://localhost:3000/login?access_token=JWT...
    ↓
登录成功
```

### 为什么是后端 8000 端口而不是前端 3000 端口？

OAuth2 回调地址必须是**后端地址**，因为：

1. **安全性**：回调处理包含敏感操作（Token 交换、用户信息获取）
2. **Second Me 验证**：Second Me 会验证回调地址是否在允许列表中
3. **API 调用**：需要调用 Second Me API 换取 Token

前端 3000 端口只负责：
- 显示登录页面
- 构造授权 URL
- 接收最终的登录结果

---

## 预防措施

### 1. 添加配置一致性检查脚本

创建 `scripts/check_oauth_config.py`：

```python
#!/usr/bin/env python3
"""
检查 OAuth2 配置一致性
"""
import os

def check_config():
    print("OAuth2 配置一致性检查")
    print("=" * 60)

    # 读取后端配置
    with open('.env', 'r', encoding='utf-8') as f:
        backend_uri = [l for l in f.readlines() if l.startswith('SECOND_ME_REDIRECT_URI')][0].strip().split('=')[1]

    # 读取前端配置
    with open('frontend/.env', 'r', encoding='utf-8') as f:
        frontend_uri = [l for l in f.readlines() if l.startswith('VITE_OAUTH_REDIRECT_URI')][0].strip().split('=')[1]

    # 读取代码中的默认值
    with open('frontend/src/api/auth.ts', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        default_line = [l for l in lines if 'OAUTH_REDIRECT_URI = ' in l][0]
        code_default = default_line.split('||')[1].strip().strip("';")

    print(f"后端配置 (.env):         {backend_uri}")
    print(f"前端配置 (frontend/.env): {frontend_uri}")
    print(f"代码默认值 (auth.ts):     {code_default}")
    print("=" * 60)

    if backend_uri == frontend_uri:
        print("✓ 后端和前端配置一致")
    else:
        print("✗ 配置不一致！")
        return False

    if backend_uri == code_default:
        print("✓ 代码默认值也一致")
    else:
        print("⚠ 代码默认值不同（如果 .env 正确则无影响）")

    return True

if __name__ == '__main__':
    success = check_config()
    exit(0 if success else 1)
```

### 2. 启动脚本自动检查

在 `package.json` 中添加：

```json
{
  "scripts": {
    "dev": "python ../scripts/check_oauth_config.py && vite"
  }
}
```

---

## 总结

**问题根源**：
- 前端 `frontend/src/api/auth.ts` 中的默认回调地址是 `http://localhost:3000/auth/callback`
- 而实际应该使用后端地址：`http://localhost:8000/api/v1/auth/callback`
- 如果前端 .env 文件未正确加载或未重启，会使用错误的默认值

**修复步骤**：
1. 确认所有配置文件正确（已完成）
2. 确认 Second Me 后台配置正确
3. 清除前端缓存并重启服务
4. 清除浏览器缓存
5. 重新测试登录流程

**关键点**：
- 回调地址必须是**后端 8000 端口**
- 前端只负责构造授权 URL 和接收最终结果
- 环境变量修改后必须**重启服务**
- 浏览器缓存会导致旧配置生效

---

**修复负责人**: Claude Code
**预计完成时间**: 15 分钟
**验证方式**: 成功完成 OAuth2 授权登录流程
