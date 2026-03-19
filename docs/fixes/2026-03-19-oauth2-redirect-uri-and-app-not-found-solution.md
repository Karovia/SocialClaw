# OAuth2 错误完整解决方案
## RedirectURL mismatch 和 Application not found

**日期**: 2026-03-19
**问题**: 登录后跳转显示 `RedirectURL mismatch` 和 `Application not found`
**状态**: 🔴 待解决

---

## 问题诊断

### 当前配置

#### 本地环境配置（.env）

```env
# Second Me 配置
SECOND_ME_CLIENT_ID=29347211-adcf-46aa-b135-128645948227
SECOND_ME_CLIENT_SECRET=3feca8c68357da1d773273024427b503986e5983527715952b187417bdd32f63
SECOND_ME_OAUTH_URL=https://go.second.me/oauth/
SECOND_ME_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback
SECOND_ME_API_BASE_URL=https://api.mindverse.com/gate/lab

# 前端地址
FRONTEND_URL=http://localhost:3000
```

#### 前端配置（frontend/.env）

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_SECOND_ME_CLIENT_ID=29347211-adcf-46aa-b135-128645948227
VITE_OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback
```

#### 后端代码（app/api/v1/auth.py）

```python
@router.get("/oauth2/login")
async def oauth2_login():
    params = {
        "client_id": settings.SECOND_ME_CLIENT_ID,
        "redirect_uri": settings.SECOND_ME_REDIRECT_URI,  # http://localhost:8000/api/v1/auth/callback
        "response_type": "code",
        "scope": "user.info,user.info.shades,user.info.softmemory"
    }
    auth_url = f"{settings.SECOND_ME_OAUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)
```

### 错误分析

出现 `RedirectURL mismatch` 和 `Application not found` 说明：

1. **App ID 不存在或已失效**
   - App ID `29347211-adcf-46aa-b135-128645948227` 可能已被删除、禁用或过期
   - Second Me 开发者平台没有找到这个应用

2. **Redirect URI 不匹配**
   - Second Me 开发者平台配置的回调地址与 `SECOND_ME_REDIRECT_URI` 不一致
   - 可能缺少 `http://` 前缀、端口号不一致、路径不匹配

3. **可能的其他原因**
   - 应用类型限制（开发环境专用）
   - 域名白名单限制
   - 权限范围配置不正确

---

## 完整解决方案

### 第一步：登录 Second Me 开发者平台

1. 访问 [https://develop.second.me](https://develop.second.me)
2. 使用你的 Second Me 账号登录
3. 进入"开发者中心"或"我的应用"

### 第二步：检查现有应用（方案 A - 复用现有应用）

1. 在应用列表中查找 App ID: `29347211-adcf-46aa-b135-128645948227`
2. 如果找到应用，检查以下配置：

#### 检查清单：

- ✅ **应用状态**: 是否为"已启用"
- ✅ **回调地址**: 是否配置为 `http://localhost:8000/api/v1/auth/callback`
- ✅ **应用类型**: 是否为"Web 应用"
- ✅ **权限范围**: 是否包含 `user.info,user.info.shades,user.info.softmemory,agent.action`
- ✅ **Secret**: 是否与本地 `.env` 文件一致
- ✅ **域名限制**: 是否允许 `localhost`

#### 如果应用配置有问题：

1. 点击应用进入编辑页面
2. 更新回调地址为：`http://localhost:8000/api/v1/auth/callback`
3. 确认权限范围包含必要权限
4. 保存更改

### 第三步：创建新应用（方案 B - 推荐）

如果找不到应用或应用已失效，创建新应用：

1. 点击"创建新应用"或"添加应用"
2. 填写应用信息：

#### 应用配置表单：

| 字段 | 值 |
|------|-----|
| **应用名称** | SocialClaw |
| **应用描述** | 去中心化的 Agent 社交网络平台 |
| **应用类型** | Web 应用 |
| **回调地址** | `http://localhost:8000/api/v1/auth/callback` |
| **权限范围** | `user.info,user.info.shades,user.info.softmemory,agent.action` |

3. 提交创建应用
4. 复制生成的 **App ID** 和 **App Secret**

### 第四步：更新本地配置

#### 更新 `.env` 文件

```env
# Second Me 配置
SECOND_ME_CLIENT_ID=<新生成的 App ID>
SECOND_ME_CLIENT_SECRET=<新生成的 App Secret>
SECOND_ME_OAUTH_URL=https://go.second.me/oauth/
SECOND_ME_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback
SECOND_ME_API_BASE_URL=https://api.mindverse.com/gate/lab
```

#### 更新 `frontend/.env` 文件

```env
# 开发环境
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_SECOND_ME_CLIENT_ID=<新生成的 App ID>
VITE_OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback
```

#### （可选）更新前端代码中的常量

检查 `frontend/src/api/auth.ts` 第 6 行：

```typescript
const OAUTH_REDIRECT_URI = import.meta.env.VITE_OAUTH_REDIRECT_URI || 'http://localhost:8000/api/v1/auth/callback';
```

### 第五步：重启后端服务

```bash
# 停止当前运行的后端服务
# 如果使用 pm2
pm2 stop socialclaw

# 如果使用 uvicorn 直接运行，按 Ctrl+C 停止

# 重新启动后端服务
cd /path/to/SocialClaw
source venv/bin/activate  # 如果使用虚拟环境
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 或者使用 pm2
pm2 start pm2.config.js
```

### 第六步：清除浏览器缓存并测试

1. 清除浏览器缓存和 Cookie
2. 访问 `http://localhost:3000`（前端）
3. 点击"使用 Second Me 登录"
4. 观察授权页面

#### 手动测试授权流程：

在浏览器中直接访问（替换 `<your-client-id>` 为实际的 App ID）：

```
https://go.second.me/oauth/?client_id=<your-client-id>&redirect_uri=http://localhost:8000/api/v1/auth/callback&response_type=code&scope=user.info,user.info.shades,user.info.softmemory
```

应该看到 Second Me 的授权页面，而不是错误信息。

### 第七步：验证完整流程

1. **授权页面**: 显示 Second Me 授权界面
2. **点击授权**: 正常跳转
3. **回调处理**: 后端处理 `/api/v1/auth/callback`
4. **重定向前端**: 跳转到 `http://localhost:3000/login?access_token=...`
5. **登录成功**: 前端显示用户信息

---

## 常见问题排查

### 问题 1: 仍然显示 `Application not found`

**可能原因**：
- App ID 输入错误
- 应用尚未创建或未保存
- 应用被删除或禁用

**解决方案**：
1. 在 Second Me 开发者平台确认应用存在
2. 复制 App ID 时不要包含空格
3. 重新创建应用

### 问题 2: 仍然显示 `RedirectURL mismatch`

**可能原因**：
- Second Me 开发者平台的回调地址与配置不一致
- 缺少 `http://` 前缀
- 端口号不一致
- 路径大小写不一致

**解决方案**：
1. 在 Second Me 开发者平台检查回调地址配置
2. 确保完全一致：`http://localhost:8000/api/v1/auth/callback`
3. 检查是否有多个回调地址，确保使用正确的
4. 配置格式（常见错误）：

❌ 错误示例：
```
localhost:8000/api/v1/auth/callback          # 缺少 http://
http://localhost:8000/callback               # 路径不匹配
http://127.0.0.1:8000/api/v1/auth/callback   # 使用了 IP 而不是 localhost
```

✅ 正确示例：
```
http://localhost:8000/api/v1/auth/callback
```

### 问题 3: 授权后回调报错 404

**可能原因**：
- 后端服务未运行
- 路由路径错误
- 端口号不正确

**解决方案**：
1. 检查后端是否运行：`curl http://localhost:8000/health`
2. 确认端口为 8000
3. 检查路由是否正确：`/api/v1/auth/callback`

### 问题 4: 前端无法接收 Token

**可能原因**：
- 前端路由未处理回调参数
- Token 在 URL hash 中但未读取

**解决方案**：
检查 `frontend/src/pages/Login.tsx` 是否处理了 URL 参数：

```typescript
useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  const token = params.get('access_token');

  if (token) {
    saveToken(token);
    // 跳转到首页
    navigate('/');
  }
}, []);
```

---

## 配置验证清单

在完成配置后，逐项验证：

- [ ] Second Me 开发者平台应用存在且已启用
- [ ] App ID 与本地 `.env` 文件一致
- [ ] App Secret 与本地 `.env` 文件一致
- [ ] 回调地址配置为 `http://localhost:8000/api/v1/auth/callback`
- [ ] 后端服务运行在 8000 端口
- [ ] 前端服务运行在 3000 端口
- [ ] 浏览器缓存已清除
- [ ] 后端配置已重新加载（重启服务）
- [ ] 前端配置已生效（重启开发服务器）

---

## 开发者平台操作截图（建议）

1. **应用列表页面**: 显示应用名称和状态
2. **应用详情页面**: 显示 App ID、Secret 和回调地址
3. **回调地址配置**: 确认地址完全一致
4. **权限范围配置**: 确认包含必要权限

---

## 参考资料

- Second Me 开发者文档：[https://develop-docs.second.me/zh/docs](https://develop-docs.second.me/zh/docs)
- OAuth2 授权流程：[https://develop-docs.second.me/zh/docs/oauth2](https://develop-docs.second.me/zh/docs/oauth2)
- 项目配置文档：[CLAUDE.md](../../CLAUDE.md)
- OAuth2 错误指南：[docs/OAuth2_ERROR_GUIDE.md](../OAuth2_ERROR_GUIDE.md)

---

## 技术支持

如仍有问题：

1. 检查 Second Me 开发者平台的应用状态
2. 查看后端日志：`tail -f logs/app.log`
3. 查看浏览器控制台错误信息
4. 检查网络请求（Network Tab）：
   - 授权请求是否成功
   - 回调请求的状态码

---

## 总结

**推荐方案**: 方案 B（创建新应用）

原因：
- 确保应用配置完全正确
- 避免旧应用的未知问题
- 获得最新的 App ID 和 Secret

**关键点**：
1. Second Me 开发者平台的回调地址必须与代码中的 `SECOND_ME_REDIRECT_URI` **完全一致**
2. App ID 和 Secret 必须与本地 `.env` 文件一致
3. 后端服务必须运行在配置的端口（8000）
4. 创建或修改应用后必须重启后端服务

**预计耗时**：10-15 分钟
