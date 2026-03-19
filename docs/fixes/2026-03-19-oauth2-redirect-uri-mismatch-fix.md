# OAuth2 Redirect URI Mismatch 问题修复方案

## 问题描述

访问 OAuth2 授权页面时显示 "Redirect URI mismatch" 错误：

```
https://second-me.cn/oauth?client_id=29347211-adcf-46aa-b135-128645948227&redirect_uri=http%3A%2F%2Flocalhost%3A8080%2Fapi%2Fv1%2Fauth%2Fcallback&response_type=code&scope=user.info%2Cuser.info.shades%2Cuser.info.softmemory
```

URL 中的 `redirect_uri` 是 `http://localhost:8080/api/v1/auth/callback`，但实际应该是 `http://localhost:8000/api/v1/auth/callback`。

## 根本原因分析

### 1. 配置不一致

检查发现三个地方的 redirect_uri 配置：

| 位置 | 当前配置 | 是否正确 |
|------|----------|----------|
| `.env` 文件 | `http://localhost:8000/api/v1/auth/callback` | ✅ 正确 |
| `config.py` 默认值 | `http://localhost:8000/auth/callback` | ❌ 缺少 `/api/v1` |
| `frontend/.env` | `http://localhost:8000/api/v1/auth/callback` | ✅ 正确 |

### 2. Pydantic 配置加载问题

`config.py` 中定义了默认值，`.env` 文件应该覆盖它。但可能由于以下原因导致配置未正确加载：

- **Pydantic 版本问题**：某些版本的 pydantic-settings 可能对环境变量覆盖有 bug
- **环境变量缓存**：之前的配置可能被缓存
- **配置加载顺序**：可能在某些情况下默认值优先级高于 .env

### 3. Second Me 后台配置

需要确认 Second Me 开发者平台中配置的回调地址是否包含：
- ✅ `http://localhost:8000/api/v1/auth/callback`

## 修复方案

### 方案 1：修改 config.py 默认值（推荐）

直接修改 `config.py` 中的默认值，确保即使 .env 未加载也能使用正确的值。

**步骤：**

1. 编辑 `app/core/config.py`，修改第 25 行：
   ```python
   # 修改前
   SECOND_ME_REDIRECT_URI: str = "http://localhost:8000/auth/callback"

   # 修改后
   SECOND_ME_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/callback"
   ```

2. 重新启动后端服务：
   ```bash
   # 停止当前服务（Ctrl+C）
   # 重新启动
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### 方案 2：清除缓存并重启

如果配置已正确但仍报错，可能是配置被缓存：

1. **清除 Python 缓存**：
   ```bash
   find . -type d -name "__pycache__" -exec rm -rf {} +
   find . -type f -name "*.pyc" -delete
   ```

2. **清除前端构建缓存**：
   ```bash
   cd frontend
   rm -rf node_modules/.vite
   npm run dev
   ```

3. **清除浏览器缓存**：
   - Chrome: `Ctrl+Shift+Delete` 清除缓存和 Cookie
   - 或使用无痕模式测试

### 方案 3：检查 Second Me 后台配置

1. 登录 Second Me 开发者平台：`https://second-me.cn`
2. 进入应用管理页面
3. 确认应用配置中的 **回调地址（Callback URL）** 包含：
   - `http://localhost:8000/api/v1/auth/callback`
4. 如果没有，添加该地址并保存

### 方案 4：调试配置加载

添加调试代码确认配置是否正确加载：

1. 在 `app/main.py` 启动时添加：
   ```python
   from app.core.config import settings

   print("=" * 60)
   print("当前配置:")
   print(f"SECOND_ME_REDIRECT_URI: {settings.SECOND_ME_REDIRECT_URI}")
   print(f"SECOND_ME_CLIENT_ID: {settings.SECOND_ME_CLIENT_ID}")
   print(f"SECOND_ME_OAUTH_URL: {settings.SECOND_ME_OAUTH_URL}")
   print("=" * 60)
   ```

2. 启动服务，查看控制台输出确认配置

## 验证步骤

### 1. 启动后端服务

```bash
cd D:/Socialclaw
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

确认控制台输出：
```
当前配置:
SECOND_ME_REDIRECT_URI: http://localhost:8000/api/v1/auth/callback
SECOND_ME_CLIENT_ID: 29347211-adcf-46aa-b135-128645948227
```

### 2. 启动前端服务

```bash
cd D:/Socialclaw/frontend
npm run dev
```

确认前端 `.env` 配置正确

### 3. 测试 OAuth2 流程

1. 访问前端页面：`http://localhost:3000`
2. 点击 "使用 Second Me 登录" 按钮
3. 检查重定向的 URL：
   ```
   https://second-me.cn/oauth?client_id=29347211-adcf-46aa-b135-128645948227&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fapi%2Fv1%2Fauth%2Fcallback&response_type=code&scope=user.info%2Cuser.info.shades%2Cuser.info.softmemory
   ```
4. 确认 `redirect_uri` 是 `http://localhost:8000/api/v1/auth/callback`（解码后）

### 4. 授权并回调

1. 在 Second Me 页面点击 "授权"
2. 应该重定向回：`http://localhost:8000/api/v1/auth/callback?code=xxx`
3. 后端处理回调，生成 JWT Token
4. 重定向到前端：`http://localhost:3000/login?access_token=xxx&user_id=xxx`

## 预防措施

### 1. 配置同步检查

在项目根目录添加 `check_config.py` 脚本：

```python
#!/usr/bin/env python3
"""
检查配置文件的一致性
"""
import os

def check_redirect_uri():
    """检查 redirect_uri 配置一致性"""

    # 读取 .env
    with open('.env', 'r', encoding='utf-8') as f:
        env_lines = f.readlines()
        env_uri = [l for l in env_lines if l.startswith('SECOND_ME_REDIRECT_URI')][0].strip().split('=')[1]

    # 读取 frontend/.env
    with open('frontend/.env', 'r', encoding='utf-8') as f:
        fenv_lines = f.readlines()
        fenv_uri = [l for l in fenv_lines if l.startswith('VITE_OAUTH_REDIRECT_URI')][0].strip().split('=')[1]

    # 检查一致性
    if env_uri == fenv_uri:
        print("✓ 配置一致")
        print(f"  后端: {env_uri}")
        print(f"  前端: {fenv_uri}")
        return True
    else:
        print("✗ 配置不一致！")
        print(f"  后端: {env_uri}")
        print(f"  前端: {fenv_uri}")
        return False

if __name__ == '__main__':
    check_redirect_uri()
```

### 2. 启动脚本

创建 `start_dev.sh`（或 Windows 版本）：

```bash
#!/bin/bash

# 检查配置
python check_config.py
if [ $? -ne 0 ]; then
    echo "配置检查失败，请修正配置后再启动"
    exit 1
fi

# 启动后端
echo "启动后端服务..."
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 启动前端
echo "启动前端服务..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# 等待
wait
```

### 3. Git Hooks

添加 pre-commit hook 检查配置一致性：

```bash
# .git/hooks/pre-commit
#!/bin/bash

python check_config.py
if [ $? -ne 0 ]; then
    echo "❌ 配置不一致，禁止提交"
    exit 1
fi

echo "✓ 配置检查通过"
```

## 常见问题

### Q1: 修改配置后仍显示旧的 redirect_uri

**原因**：配置被缓存或服务未重启

**解决**：
1. 停止所有服务
2. 清除 Python 缓存：`find . -type d -name "__pycache__" -exec rm -rf {} +`
3. 重新启动服务

### Q2: Second Me 后台没有添加回调地址

**解决**：
1. 登录 Second Me 开发者平台
2. 进入应用设置
3. 在 "回调地址" 或 "Redirect URI" 字段添加：
   - `http://localhost:8000/api/v1/auth/callback`
4. 保存配置

### Q3: 多个 redirect_uri 如何配置

如果需要支持多个环境（开发、测试、生产），可以在 Second Me 后台添加多个回调地址：

```
http://localhost:8000/api/v1/auth/callback
http://test.socialclaw.com/api/v1/auth/callback
https://socialclaw.com/api/v1/auth/callback
```

## 总结

**核心问题**：`config.py` 中的默认值缺少 `/api/v1` 路径

**解决方案**：
1. 修改 `app/core/config.py` 第 25 行，添加 `/api/v1` 路径
2. 重新启动后端服务
3. 清除浏览器缓存
4. 确认 Second Me 后台配置正确

**预防措施**：
- 添加配置一致性检查脚本
- 使用 Git hooks 防止配置不一致提交
- 添加启动脚本自动检查配置

---

**文档创建时间**: 2026-03-19
**修复人员**: Claude Code
**验证状态**: 待验证
