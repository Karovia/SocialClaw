# OAuth2 错误排查 - 双重错误分析
## Application not found + RedirectURL mismatch

**日期**: 2026-03-19
**错误**: `Application not found` + `RedirectURL mismatch`
**状态**: 🔴 需要人工干预

---

## 错误分析

### 错误组合含义

同时出现两个错误，说明：

1. **App ID 无效**
   - App ID `9840cef2-9db2-44f9-9c80-e55a3fb31eb2` 不存在于 Second Me 开发者平台
   - 或应用未启用
   - 或应用属于其他开发者账号

2. **回调地址验证失败**
   - 因为 App ID 无效，系统无法检查回调地址配置
   - 所以同时显示两个错误

### 可能原因

| 原因 | 概率 | 说明 |
|------|------|------|
| App ID 不存在 | 高 | 复制的 ID 不正确或应用已被删除 |
| 应用未启用 | 中 | 应用存在但状态为"禁用" |
| 账号不匹配 | 中 | 应用属于其他 Second Me 账号 |
| 配置错误 | 低 | 回调地址配置不正确 |

---

## 解决方案

### 方案 1: 检查现有应用（如果应用应该存在）

**操作步骤**:

1. **登录 Second Me 开发者平台**
   - 访问: https://develop.second.me
   - 使用 Second Me 账号登录

2. **查找应用**
   - 进入"我的应用"或"开发者中心"
   - 查找 App ID: `9840cef2-9db2-44f9-9c80-e55a3fb31eb2`
   - 或搜索应用名称 "SocialClaw"

3. **检查应用配置**
   - 应用状态: 启用/禁用
   - 回调地址: 是否为 `http://localhost:8000/api/v1/auth/callback`
   - App Secret: 对比本地配置

4. **反馈信息**
   - [ ] 应用是否找到？
   - [ ] 应用状态是什么？
   - [ ] 配置的回调地址是什么？
   - [ ] 截图应用详情页面

### 方案 2: 创建新应用（推荐）

**操作步骤**:

1. **登录 Second Me 开发者平台**
   - 访问: https://develop.second.me
   - 使用 Second Me 账号登录

2. **创建新应用**
   - 点击"创建新应用"或"添加应用"
   - 填写应用信息:

#### 应用配置表单

| 字段 | 填写内容 |
|------|---------|
| **应用名称** | SocialClaw |
| **应用描述** | 去中心化的 Agent 社交网络平台 |
| **应用类型** | Web 应用 |
| **回调地址** | `http://localhost:8000/api/v1/auth/callback` |
| **权限范围** | `user.info,user.info.shades,user.info.softmemory,agent.action` |

3. **获取新凭证**
   - 提交创建后，系统生成新的 App ID 和 Secret
   - **复制并保存**:
     - 新的 App ID: _______________
     - 新的 App Secret: _______________

4. **反馈新凭证**
   - 将新的 App ID 和 Secret 反馈给我
   - 我会立即更新配置并重启服务

---

## 手动测试链接

创建应用后，使用新 App ID 测试：

```
https://go.second.me/oauth/?client_id=<新AppID>&redirect_uri=http://localhost:8000/api/v1/auth/callback&response_type=code&scope=user.info,user.info.shades,user.info.softmemory
```

---

## 配置验证清单

创建应用后，确保以下配置完全一致：

| 配置项 | 后端 (.env) | 前端 (frontend/.env) | Second Me 平台 | 状态 |
|--------|------------|---------------------|---------------|------|
| App ID | 9840cef2-... | 9840cef2-... | 9840cef2-... | ⚠️ 需确认 |
| Redirect URI | http://localhost:8000/api/v1/auth/callback | http://localhost:8000/api/v1/auth/callback | http://localhost:8000/api/v1/auth/callback | ⚠️ 需确认 |
| Callback URL | /api/v1/auth/callback | /api/v1/auth/callback | /api/v1/auth/callback | ✅ 一致 |

---

## 常见问题

### Q1: 找不到应用怎么办？
**A**: 直接创建新应用，使用新生成的 App ID 和 Secret。

### Q2: 应用状态是"禁用"？
**A**: 在应用详情页面点击"启用"按钮。

### Q3: 回调地址配置不正确？
**A**: 编辑应用，将回调地址修改为 `http://localhost:8000/api/v1/auth/callback`。

### Q4: 有多个回调地址选项？
**A**: 确保至少有一个是 `http://localhost:8000/api/v1/auth/callback`。

---

## 下一步

**请执行以下操作之一**:

1. **方案 1**: 登录开发者平台检查现有应用，并反馈检查结果
2. **方案 2**: 直接创建新应用，并反馈新的 App ID 和 Secret

**反馈格式**:

```
方案选择: [方案1/方案2]

如果是方案1:
- 应用是否找到: [是/否]
- 应用状态: [启用/禁用]
- 回调地址配置: [实际配置的地址]
- 截图: [有/无]

如果是方案2:
- 新的 App ID: _______________
- 新的 App Secret: _______________
```

---

## 参考资料

- Second Me 开发者平台: https://develop.second.me
- Second Me 开发者文档: https://develop-docs.second.me/zh/docs
- OAuth2 授权流程: https://develop-docs.second.me/zh/docs/oauth2
