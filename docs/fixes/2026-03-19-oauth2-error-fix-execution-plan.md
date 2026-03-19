# OAuth2 错误修复执行计划
## RedirectURL mismatch 和 Application not found

**日期**: 2026-03-19
**执行人**: AI Agent
**状态**: 🟡 进行中

---

## 当前配置

### 后端配置 (.env)

```env
SECOND_ME_CLIENT_ID=29347211-adcf-46aa-b135-128645948227
SECOND_ME_CLIENT_SECRET=3feca8c68357da1d773273024427b503986e5983527715952b187417bdd32f63
SECOND_ME_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback
SECOND_ME_OAUTH_URL=https://go.second.me/oauth/
FRONTEND_URL=http://localhost:3000
```

### 前端配置 (frontend/.env)

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_SECOND_ME_CLIENT_ID=29347211-adcf-46aa-b135-128645948227
VITE_OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback
```

### 授权 URL 格式

```
https://go.second.me/oauth/?
  client_id=29347211-adcf-46aa-b135-128645948227
  &redirect_uri=http://localhost:8000/api/v1/auth/callback
  &response_type=code
  &scope=user.info,user.info.shades,user.info.softmemory
```

---

## 执行步骤

### ✅ 步骤 1: 验证后端服务状态

**状态**: 已完成
**结果**: 后端服务运行在 8000 端口（进程: 30984, 9700, 9112）

**验证命令**:
```bash
netstat -ano | findstr :8000
```

**下一步**: 手动测试授权流程

---

### ⏳ 步骤 2: 手动测试 OAuth2 授权

**操作**: 在浏览器中访问以下 URL

```
https://go.second.me/oauth/?client_id=29347211-adcf-46aa-b135-128645948227&redirect_uri=http://localhost:8000/api/v1/auth/callback&response_type=code&scope=user.info,user.info.shades,user.info.softmemory
```

**预期结果**:
- ✅ 成功: 显示 Second Me 授权页面
- ❌ 失败: 显示错误信息

**需要记录的错误**:
1. `Application not found` - 应用不存在
2. `RedirectURL mismatch` - 回调地址不匹配
3. 其他错误信息

**下一步**: 根据错误类型采取不同方案

---

### 📋 步骤 3: 检查 Second Me 开发者平台（需要人工操作）

**需要用户执行**:

1. **登录开发者平台**
   - 访问: [https://develop.second.me](https://develop.second.me)
   - 使用 Second Me 账号登录

2. **查找现有应用**
   - 进入"我的应用"或"开发者中心"
   - 查找 App ID: `29347211-adcf-46aa-b135-128645948227`
   - 如果找到，记录以下信息:
     - 应用状态（启用/禁用）
     - 配置的回调地址
     - 权限范围
     - App Secret（对比本地配置）

3. **如果应用不存在或已失效**
   - 点击"创建新应用"
   - 填写应用信息:
     - 应用名称: SocialClaw
     - 应用类型: Web 应用
     - 回调地址: `http://localhost:8000/api/v1/auth/callback`
     - 权限范围: `user.info,user.info.shades,user.info.softmemory,agent.action`
   - 复制生成的 App ID 和 Secret

**输出**:
- [ ] 应用存在且配置正确
- [ ] 应用存在但配置有问题
- [ ] 应用不存在/已失效
- [ ] 已创建新应用（新 App ID: _______）

---

### ⚙️ 步骤 4: 更新配置文件

**条件**: 如果步骤 3 中创建了新应用

**操作 1: 更新后端 .env**

```bash
# 如果创建了新应用，更新以下配置
SECOND_ME_CLIENT_ID=<新AppID>
SECOND_ME_CLIENT_SECRET=<新Secret>
```

**操作 2: 更新前端 frontend/.env**

```bash
VITE_SECOND_ME_CLIENT_ID=<新AppID>
```

**验证**:
- [ ] 后端 .env 已更新
- [ ] 前端 frontend/.env 已更新

---

### 🔄 步骤 5: 重启后端服务

**操作**:

1. **停止当前服务**
   - 如果使用 pm2: `pm2 stop socialclaw`
   - 如果直接运行: 按 Ctrl+C

2. **重新启动服务**
   ```bash
   cd D:\SocialClaw
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **验证服务启动**
   - 访问: `http://localhost:8000/docs`（查看 API 文档）
   - 检查日志无错误

**验证**:
- [ ] 后端服务已重启
- [ ] 可访问 http://localhost:8000/docs
- [ ] 日志无错误

---

### 🧪 步骤 6: 测试完整登录流程

**操作**:

1. **清除浏览器缓存**
   - Chrome: Ctrl+Shift+Delete
   - Firefox: Ctrl+Shift+Delete
   - Edge: Ctrl+Shift+Delete

2. **访问前端页面**
   - 访问: `http://localhost:3000`
   - 确保前端服务正在运行

3. **点击登录**
   - 点击"使用 Second Me 登录"按钮
   - 观察跳转页面

4. **授权页面**
   - 应显示 Second Me 授权页面
   - 点击"授权"按钮

5. **回调处理**
   - 应跳转回 `http://localhost:3000/login?access_token=...`
   - 前端应保存 Token 并跳转到首页

**验证**:
- [ ] 授权页面正常显示
- [ ] 授权成功后跳转到前端
- [ ] Token 成功保存
- [ ] 用户信息正确显示

---

### 📊 步骤 7: 检查日志和错误信息

**后端日志位置**: `logs/app.log`

**需要检查的内容**:

1. **OAuth2 登录请求**
   ```log
   [INFO] OAuth2 login request received
   [INFO] Redirecting to: https://go.second.me/oauth/?client_id=...
   ```

2. **OAuth2 回调处理**
   ```log
   [INFO] OAuth2 callback received
   [INFO] Exchanging code for token...
   [INFO] Token exchange successful
   [INFO] Getting user info...
   [INFO] User info retrieved: userId=labs_user_xxx
   [INFO] Creating/updating user: soc_user_labs_user_xxx
   [INFO] Redirecting to frontend: http://localhost:3000/login?access_token=...
   ```

3. **错误日志**
   ```log
   [ERROR] OAuth2 callback failed: ...
   ```

**常见错误**:
- `Token exchange failed` - Second Me Token 交换失败
- `Get user info failed` - 获取用户信息失败
- `Invalid client_id or client_secret` - App ID 或 Secret 错误

---

### ✅ 步骤 8: 验证配置一致性

**检查清单**:

- [ ] Second Me 开发者平台的回调地址 = `http://localhost:8000/api/v1/auth/callback`
- [ ] 后端 .env 的 `SECOND_ME_REDIRECT_URI` = `http://localhost:8000/api/v1/auth/callback`
- [ ] 前端 .env 的 `VITE_OAUTH_REDIRECT_URI` = `http://localhost:8000/api/v1/auth/callback`
- [ ] 后端 .env 的 `SECOND_ME_CLIENT_ID` 与 Second Me 开发者平台一致
- [ ] 前端 .env 的 `VITE_SECOND_ME_CLIENT_ID` 与后端一致
- [ ] Second Me 开发者平台的应用状态为"启用"

---

### 🎯 成功标准

登录流程完整执行后：

1. ✅ 用户点击"使用 Second Me 登录"
2. ✅ 跳转到 Second Me 授权页面
3. ✅ 显示授权页面（无错误）
4. ✅ 点击"授权"按钮
5. ✅ 回调到后端 `/api/v1/auth/callback`
6. ✅ 后端处理成功
7. ✅ 重定向前端并携带 Token
8. ✅ 前端保存 Token 并显示用户信息

---

## 可能的问题和解决方案

### 问题 1: `Application not found`

**原因**: App ID 不存在或已失效

**解决方案**:
1. 登录 Second Me 开发者平台
2. 创建新应用
3. 更新本地配置
4. 重启后端服务

### 问题 2: `RedirectURL mismatch`

**原因**: Second Me 开发者平台配置的回调地址与代码不一致

**解决方案**:
1. 登录 Second Me 开发者平台
2. 检查并更新回调地址为: `http://localhost:8000/api/v1/auth/callback`
3. 确保完全一致（包括大小写、端口号）
4. 保存配置

### 问题 3: 授权后回调 404

**原因**: 后端路由未正确配置或服务未运行

**解决方案**:
1. 检查后端是否运行: `curl http://localhost:8000/health`
2. 确认路由存在: `/api/v1/auth/callback`
3. 检查路由前缀配置

### 问题 4: Token 交换失败

**原因**: App Secret 错误或 Second Me API 返回错误

**解决方案**:
1. 检查 Second Me 开发者平台的 App Secret
2. 更新本地 .env 文件
3. 重启后端服务
4. 检查 Second Me API 文档确认格式

---

## 参考文档

- [OAuth2 错误完整解决方案](./2026-03-19-oauth2-redirect-uri-and-app-not-found-solution.md)
- [OAuth2 错误排查指南](../OAuth2_ERROR_GUIDE.md)
- Second Me 开发者文档: [https://develop-docs.second.me/zh/docs](https://develop-docs.second.me/zh/docs)

---

## 下一步行动

当前进度: **步骤 2 - 手动测试 OAuth2 授权**

**需要用户执行**:
1. 在浏览器中访问手动测试链接
2. 记录显示的错误信息或成功页面
3. 反馈结果以便继续后续步骤

**后续步骤**:
- 如果成功: 继续步骤 6（完整登录测试）
- 如果失败: 根据错误类型执行步骤 3（检查开发者平台）

---

## 执行历史

| 步骤 | 状态 | 时间 | 说明 |
|------|------|------|------|
| 1. 验证后端服务 | ✅ 完成 | 2026-03-19 | 8000 端口已占用 |
| 2. 手动测试授权 | ⏳ 进行中 | 2026-03-19 | 等待用户反馈 |
| 3. 检查开发者平台 | ⏳ 待执行 | - | 需要人工操作 |
| 4. 更新配置 | ⏳ 待执行 | - | 根据步骤 3 结果 |
| 5. 重启后端 | ⏳ 待执行 | - | 配置更新后 |
| 6. 完整测试 | ⏳ 待执行 | - | 配置验证后 |
| 7. 检查日志 | ⏳ 待执行 | - | 测试过程中 |
| 8. 验证一致性 | ⏳ 待执行 | - | 最终验证 |
