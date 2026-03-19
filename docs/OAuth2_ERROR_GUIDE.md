# OAuth2 错误排查指南

## 错误信息
- `application not found` - 应用不存在
- `Redirect URL mismatch` - 回调地址不匹配

## 可能原因

### 1. App ID 或 Secret 错误
当前配置：
- Client ID: `29347211-adcf-46aa-b135-128645948227`
- Client Secret: `3feca8c68357da1d773273024427b503986e5983527715952b187417bdd32f63`
- Redirect URI: `http://localhost:8000/api/v1/auth/callback`

### 2. Second Me 应用状态问题
- 应用可能已被删除
- 应用可能已被禁用
- 应用可能过期

### 3. 回调地址配置问题
- Second Me 开发者平台配置的回调地址与实际不一致
- 可能缺少 `http://` 前缀
- 可能端口号不一致

### 4. 应用类型限制
- 应用可能是开发环境专用
- 应用可能有域名白名单限制

## 排查步骤

### 步骤 1：访问 Second Me 开发者平台
1. 打开 https://develop.second.me
2. 登录账号
3. 进入"我的应用"或"开发者中心"
4. 检查 App ID `29347211-adcf-46aa-b135-128645948227` 是否存在
5. 检查应用状态（启用/禁用）
6. 检查回调地址配置是否为：`http://localhost:8000/api/v1/auth/callback`

### 步骤 2：手动测试授权
在浏览器中直接访问：
```
https://go.second.me/oauth/?client_id=29347211-adcf-46aa-b135-128645948227&redirect_uri=http://localhost:8000/api/v1/auth/callback&response_type=code&scope=user.info,user.info.shades,user.info.softmemory
```

记录显示的具体错误信息。

### 步骤 3：创建新应用（如果应用失效）
1. 在 Second Me 开发者平台创建新应用
2. 填写应用名称：SocialClaw
3. 应用类型：Web 应用
4. 回调地址：`http://localhost:8000/api/v1/auth/callback`
5. 权限范围：`user.info,user.info.shades,user.info.softmemory,agent.action`
6. 复制新的 App ID 和 Secret
7. 更新 `.env` 文件

### 步骤 4：检查后端是否运行
```bash
# 检查后端是否在 8000 端口运行
curl http://localhost:8000/health
```

## 解决方案

### 方案 A：重新创建应用
如果应用已失效，最简单的方案是创建新应用。

### 方案 B：修改回调地址
如果回调地址配置错误，修改 Second Me 开发者平台的回调地址配置。

### 方案 C：检查应用权限
确保应用已启用，并且权限范围正确。

## 技术支持
- Second Me 开发者文档：https://develop-docs.second.me/zh/docs
- Second Me 开发者平台：https://develop.second.me
