# SocialClaw 模块 1: 认证与用户管理实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现完整的 Second Me OAuth2 授权登录、用户信息管理和 Token 刷新功能

**Architecture:**
- 使用 FastAPI 构建 OAuth2 授权路由和回调处理
- 实现 auth_service 处理 Second Me Token 交换和用户创建/获取
- JWT Token 用于 SocialClaw 内部认证（与 Second Me Token 分离）
- 所有敏感操作（Token 交换、用户信息获取）通过 HTTPX 异步调用 Second Me API

**Tech Stack:** FastAPI 0.115.0, SQLAlchemy 2.0, HTTPX, JWT (python-jose), OAuth2

**Second Me API 参考:** @secondme-reference（已加载到记忆中）

---

## 文件结构概览

| 文件路径 | 职责 | 状态 |
|---------|------|------|
| `app/services/auth_service.py` | 认证业务逻辑（Token 交换、用户信息获取、用户创建/获取、Token 刷新） | 待创建 |
| `app/api/v1/auth.py` | OAuth2 授权路由（登录重定向、回调处理、Token 刷新） | 待创建 |
| `app/api/v1/users.py` | 用户信息路由（获取当前用户信息） | 待创建 |
| `app/core/auth.py` | JWT Token 生成/验证、依赖注入（`get_current_user`） | 已存在（需验证） |
| `app/core/config.py` | 配置管理（Second Me Client ID/Secret/URL 等） | 已存在（需验证） |
| `tests/test_auth_oauth2.py` | OAuth2 登录路由测试 | 待创建 |
| `tests/test_auth_callback.py` | OAuth2 回调处理集成测试 | 待创建 |
| `tests/test_auth_service.py` | 认证服务单元测试 | 待创建 |
| `tests/test_users.py` | 用户信息路由测试 | 待创建 |

---

## 开发前准备

### 验证现有配置文件

- [ ] **Step 0.1: 检查并完善环境变量配置**

```bash
# 检查 .env 文件是否包含所有必需配置
cat .env
```

必需配置项：
```env
# Second Me 配置
SECOND_ME_CLIENT_ID=29347211-adcf-46aa-b135-128645948227
SECOND_ME_CLIENT_SECRET=3feca8c68357da1d773273024427b503986e5983527715952b187417bdd32f63
SECOND_ME_REDIRECT_URI=http://localhost:8000/auth/callback
SECOND_ME_OAUTH_URL=https://go.second.me/oauth/
SECOND_ME_API_BASE_URL=https://api.mindverse.com/gate/lab

# JWT 配置
SECRET_KEY=your-secret-key-here  # 必须设置为随机字符串
JWT_EXPIRE_HOURS=24

# 数据库
DATABASE_URL=sqlite:///./data/sqlite/socialclaw.db
```

- [ ] **Step 0.2: 验证 `app/core/config.py` 是否正确加载这些配置**

```python
# 确保 config.py 包含以下字段
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Second Me 配置
    SECOND_ME_CLIENT_ID: str
    SECOND_ME_CLIENT_SECRET: str
    SECOND_ME_REDIRECT_URI: str
    SECOND_ME_OAUTH_URL: str = "https://go.second.me/oauth/"
    SECOND_ME_API_BASE_URL: str = "https://api.mindverse.com/gate/lab"

    # JWT 配置
    SECRET_KEY: str
    JWT_EXPIRE_HOURS: int = 24

    # 数据库
    DATABASE_URL: str = "sqlite:///./data/sqlite/socialclaw.db"

    class Config:
        env_file = ".env"
```

- [ ] **Step 0.3: 验证 `app/core/auth.py` 是否包含 JWT 工具函数**

```python
# 确保 auth.py 包含以下函数
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.database import get_db

# JWT 配置
ALGORITHM = "HS256"
security = HTTPBearer()

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """生成 JWT Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict]:
    """解码 JWT Token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前认证用户（依赖注入）"""
    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
        )

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return user
```

- [ ] **Step 0.4: 验证数据库模型**

确保以下模型已正确定义：
- `app/models/user.py` - User 模型（`user_id`, `second_me_user_id`, `email`, `username`, `avatar_url`, `created_at`, `updated_at`）
- `app/models/second_me_binding.py` - SecondMeBinding 模型（`binding_id`, `user_id`, `second_me_user_id`, `access_token`, `refresh_token`, `expires_at`, `scope`, `bound_at`）

- [ ] **Step 0.5: 运行数据库迁移（如果需要）**

```bash
# 如果数据库文件不存在，运行初始化
python -c "
from app.database import engine
from app.models import Base
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
"
```

---

## Task 1: 实现 OAuth2 授权登录路由

**Files:**
- Create: `app/api/v1/auth.py`
- Test: `tests/test_auth_oauth2.py`

### 1.1 创建 OAuth2 登录路由测试

- [ ] **Step 1: 创建测试文件 `tests/test_auth_oauth2.py`**

```python
"""
OAuth2 授权登录路由测试
测试用例：
- 验证登录重定向 URL 是否正确
- 验证 URL 参数是否完整（client_id, redirect_uri, response_type, scope）
"""
import pytest
from fastapi.testclient import TestClient
from urllib.parse import urlparse, parse_qs

# 导入应用（假设 app 在 app.main 中）
from app.main import app


class TestOAuth2Login:
    """OAuth2 登录重定向测试"""

    def test_oauth2_login_redirect(self):
        """测试 OAuth2 登录重定向到 Second Me"""
        client = TestClient(app)

        response = client.get("/api/v1/auth/oauth2/login")

        # 验证状态码
        assert response.status_code == 302, f"Expected 302 redirect, got {response.status_code}"

        # 验证 Location header
        location = response.headers.get("location")
        assert location is not None, "Location header is missing"

        # 验证 URL 格式
        parsed_url = urlparse(location)
        assert parsed_url.netloc == "go.second.me", f"Expected go.second.me, got {parsed_url.netloc}"
        assert parsed_url.path == "/oauth/", f"Expected /oauth/, got {parsed_url.path}"

        # 验证查询参数
        query_params = parse_qs(parsed_url.query)

        # client_id 必须存在且正确
        assert "client_id" in query_params, "client_id parameter is missing"
        assert query_params["client_id"][0] == "29347211-adcf-46aa-b135-128645948227"

        # redirect_uri 必须存在
        assert "redirect_uri" in query_params, "redirect_uri parameter is missing"
        assert query_params["redirect_uri"][0] == "http://localhost:8000/auth/callback"

        # response_type 必须是 code
        assert "response_type" in query_params, "response_type parameter is missing"
        assert query_params["response_type"][0] == "code"

        # scope 必须包含必需的权限
        assert "scope" in query_params, "scope parameter is missing"
        scopes = query_params["scope"][0].split(",")
        assert "user.info" in scopes
        assert "user.info.shades" in scopes
        assert "user.info.softmemory" in scopes

        print(f"✓ OAuth2 login redirect URL: {location}")

    def test_oauth2_login_url_structure(self):
        """测试 OAuth2 URL 结构（不含 /authorize 等多余路径）"""
        client = TestClient(app)

        response = client.get("/api/v1/auth/oauth2/login")
        location = response.headers.get("location")
        parsed_url = urlparse(location)

        # URL 必须是 https://go.second.me/oauth/?xxx 格式
        # 不能是 https://go.second.me/oauth//authorize?xxx
        assert not parsed_url.path.endswith("/authorize"), \
            "OAuth2 URL should not contain /authorize suffix"
        assert parsed_url.path == "/oauth/", \
            "OAuth2 URL path should be exactly /oauth/"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_auth_oauth2.py::TestOAuth2Login::test_oauth2_login_redirect -v
```

Expected output:
```
FAILED tests/test_auth_oauth2.py::TestOAuth2Login::test_oauth2_login_redirect - 404 Not Found
```

---

### 1.2 实现 OAuth2 授权路由

- [ ] **Step 3: 创建 `app/api/v1/auth.py`**

```python
"""
OAuth2 认证路由
提供：
- OAuth2 登录重定向
- OAuth2 回调处理
- Token 刷新
"""
from fastapi import APIRouter, Request, Query, Depends, HTTPException
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
from typing import Optional
from datetime import datetime

from app.core.config import settings
from app.core.auth import get_current_user
from app.models.user import User
from app.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/oauth2/login")
async def oauth2_login():
    """
    跳转到 Second Me OAuth2 授权页面

    流程：
    1. 构造 OAuth2 授权 URL
    2. 重定向用户到 Second Me 授权页面

    URL 格式：
    https://go.second.me/oauth/?client_id=xxx&redirect_uri=xxx&response_type=code&scope=xxx

    注意：不要在 URL 后面追加 /authorize 等路径
    """
    # 构造授权参数
    params = {
        "client_id": settings.SECOND_ME_CLIENT_ID,
        "redirect_uri": settings.SECOND_ME_REDIRECT_URI,
        "response_type": "code",
        "scope": "user.info,user.info.shades,user.info.softmemory"
    }

    # 构造完整的授权 URL
    # ✅ 正确：直接拼接 ? 和参数
    auth_url = f"{settings.SECOND_ME_OAUTH_URL}?{urlencode(params)}"

    # ❌ 错误：不要追加 /authorize 等路径
    # auth_url = f"{settings.SECOND_ME_OAUTH_URL}/authorize?{urlencode(params)}"

    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def oauth2_callback(
    code: str = Query(..., description="Second Me 授权码"),
    db: Session = Depends(get_db)
):
    """
    OAuth2 回调处理

    流程：
    1. 使用 authorization_code 换取 Second Me access_token
    2. 使用 access_token 获取用户信息
    3. 创建或获取 SocialClaw 用户账号
    4. 保存 Second Me 绑定信息
    5. 生成 JWT Token 并返回

    Parameters:
    - code: Second Me 授权码（有效期 5 分钟）

    Returns:
    - access_token: SocialClaw JWT Token
    - user_info: 用户信息
    """
    from app.services.auth_service import (
        exchange_code_for_token,
        get_user_info,
        create_or_get_user
    )
    from app.core.auth import create_access_token

    try:
        # 1. 用 code 换取 Second Me Token
        second_me_tokens = await exchange_code_for_token(code)

        # 2. 获取用户信息
        user_info = await get_user_info(second_me_tokens["access_token"])

        # 3. 创建或获取用户
        user = await create_or_get_user(db, user_info, second_me_tokens)

        # 4. 生成 JWT Token
        jwt_token = create_access_token(
            data={
                "user_id": user.user_id,
                "second_me_user_id": user.second_me_user_id,
                "email": user.email
            }
        )

        return {
            "code": 0,
            "data": {
                "access_token": jwt_token,
                "token_type": "bearer",
                "expires_in": 86400,  # 24 小时
                "user_info": {
                    "user_id": user.user_id,
                    "second_me_user_id": user.second_me_user_id,
                    "email": user.email,
                    "username": user.username,
                    "avatar_url": user.avatar_url,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"OAuth2 授权失败: {str(e)}"
        )


@router.post("/refresh")
async def refresh_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    刷新 JWT Token

    流程：
    1. 获取用户的 Second Me refresh_token
    2. 检查 Second Me access_token 是否过期
    3. 如果过期，使用 refresh_token 刷新 Second Me Token
    4. 更新数据库中的绑定信息
    5. 生成新的 JWT Token 并返回

    注意：
    - Second Me Access Token 有效期：2 小时
    - Second Me Refresh Token 有效期：30 天
    - SocialClaw JWT Token 有效期：24 小时
    """
    from app.services.auth_service import refresh_second_me_token
    from app.models.second_me_binding import SecondMeBinding
    from datetime import timedelta

    # 获取用户的 Second Me 绑定信息
    binding = db.query(SecondMeBinding).filter(
        SecondMeBinding.user_id == current_user.user_id
    ).first()

    if not binding:
        raise HTTPException(status_code=400, detail="用户未绑定 Second Me 账号")

    # 检查 Second Me access_token 是否过期
    if binding.expires_at and binding.expires_at < datetime.utcnow():
        # 使用 refresh_token 刷新 Second Me Token
        try:
            new_tokens = await refresh_second_me_token(binding.refresh_token)

            # 更新数据库
            binding.access_token = new_tokens["access_token"]
            binding.refresh_token = new_tokens["refresh_token"]
            binding.expires_at = datetime.utcnow() + timedelta(seconds=new_tokens["expires_in"])
            db.commit()

            print(f"✓ Refreshed Second Me token for user {current_user.user_id}")

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"刷新 Second Me Token 失败: {str(e)}"
            )

    # 生成新的 SocialClaw JWT Token
    new_jwt = create_access_token(
        data={
            "user_id": current_user.user_id,
            "second_me_user_id": current_user.second_me_user_id,
            "email": current_user.email
        }
    )

    return {
        "code": 0,
        "data": {
            "access_token": new_jwt,
            "expires_in": 86400,
            "message": "Token 已刷新"
        }
    }
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_auth_oauth2.py -v
```

Expected output:
```
PASSED tests/test_auth_oauth2.py::TestOAuth2Login::test_oauth2_login_redirect
PASSED tests/test_auth_oauth2.py::TestOAuth2Login::test_oauth2_login_url_structure
```

- [ ] **Step 5: 提交代码**

```bash
git add app/api/v1/auth.py tests/test_auth_oauth2.py
git commit -m "feat(auth): add OAuth2 login redirect endpoint"
```

---

## Task 2: 实现认证服务层（Token 交换、用户信息、用户创建）

**Files:**
- Create: `app/services/auth_service.py`
- Test: `tests/test_auth_service.py`

### 2.1 创建认证服务单元测试

- [ ] **Step 1: 创建测试文件 `tests/test_auth_service.py`**

```python
"""
认证服务单元测试
测试用例：
- Token 交换（code -> access_token + refresh_token）
- 获取用户信息
- 创建新用户
- 获取已存在用户
- 刷新 Token
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# 导入待测试的服务
from app.services.auth_service import (
    exchange_code_for_token,
    get_user_info,
    create_or_get_user,
    refresh_second_me_token
)


class TestAuthService:
    """认证服务测试"""

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_success(self):
        """测试用 code 成功换取 Token"""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock HTTPX 响应
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "code": 0,
                "data": {
                    "accessToken": "lba_at_test_12345",
                    "refreshToken": "lba_rt_test_67890",
                    "tokenType": "Bearer",
                    "expiresIn": 7200
                }
            }
            mock_response.status_code = 200

            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response
            mock_client.return_value = mock_instance

            # 调用服务
            result = await exchange_code_for_token("test_auth_code")

            # 验证结果
            assert result["access_token"] == "lba_at_test_12345"
            assert result["refresh_token"] == "lba_rt_test_67890"
            assert result["expires_in"] == 7200

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_failure(self):
        """测试 Token 交换失败（无效 code）"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "code": 1,
                "message": "Invalid authorization code",
                "errorCode": "oauth.invalid_code"
            }
            mock_response.status_code = 400

            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response
            mock_client.return_value = mock_instance

            # 调用服务，应该抛出异常
            with pytest.raises(Exception) as exc_info:
                await exchange_code_for_token("invalid_code")

            assert "Token exchange failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_user_info_success(self):
        """测试成功获取用户信息"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "code": 0,
                "data": {
                    "userId": "labs_user_test123",
                    "email": "user@example.com",
                    "name": "测试用户",
                    "avatarUrl": "https://example.com/avatar.jpg",
                    "route": "testuser"
                }
            }
            mock_response.status_code = 200

            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.get.return_value = mock_response
            mock_client.return_value = mock_instance

            # 调用服务
            result = await get_user_info("lba_at_test_token")

            # 验证结果
            assert result["userId"] == "labs_user_test123"
            assert result["email"] == "user@example.com"
            assert result["name"] == "测试用户"
            assert result["avatarUrl"] == "https://example.com/avatar.jpg"

    @pytest.mark.asyncio
    async def test_refresh_token_success(self):
        """测试成功刷新 Token"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "code": 0,
                "data": {
                    "accessToken": "lba_at_new_token",
                    "refreshToken": "lba_rt_new_token",
                    "expiresIn": 7200
                }
            }
            mock_response.status_code = 200

            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response
            mock_client.return_value = mock_instance

            # 调用服务
            result = await refresh_second_me_token("lba_rt_old_token")

            # 验证结果
            assert result["access_token"] == "lba_at_new_token"
            assert result["refresh_token"] == "lba_rt_new_token"
            assert result["expires_in"] == 7200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_auth_service.py -v
```

Expected output:
```
FAILED tests/test_auth_service.py::TestAuthService::test_exchange_code_for_token_success - ModuleNotFoundError: No module named 'app.services.auth_service'
```

---

### 2.2 实现认证服务

- [ ] **Step 3: 创建 `app/services/auth_service.py`**

```python
"""
认证服务层
负责：
- Second Me Token 交换（code -> access_token）
- Second Me Token 刷新（refresh_token -> new access_token）
- 获取 Second Me 用户信息
- 创建/获取 SocialClaw 用户账号
- 管理 Second Me 绑定信息

注意：
- 所有 Second Me API 响应都使用 camelCase（accessToken, refreshToken）
- 所有 SocialClaw 内部使用 snake_case（access_token, refresh_token）
- Token 有效期：
  - Second Me Access Token: 2 小时
  - Second Me Refresh Token: 30 天
  - SocialClaw JWT Token: 24 小时
"""
import httpx
from typing import Dict, Optional
from datetime import datetime, timedelta
import uuid

from app.core.config import settings
from app.models.user import User
from app.models.second_me_binding import SecondMeBinding
from sqlalchemy.orm import Session


async def exchange_code_for_token(code: str) -> Dict:
    """
    用授权码换取 Second Me Token

    OAuth2 流程步骤 2：
    POST /api/oauth/token/code

    请求格式：
    Content-Type: application/x-www-form-urlencoded
    grant_type=authorization_code
    &code={code}
    &redirect_uri={redirect_uri}
    &client_id={client_id}
    &client_secret={client_secret}

    响应格式：
    {
      "code": 0,
      "data": {
        "accessToken": "lba_at_xxx",
        "refreshToken": "lba_rt_xxx",
        "expiresIn": 7200
      }
    }

    Args:
        code: Second Me 授权码（有效期 5 分钟）

    Returns:
        Dict: 包含 access_token, refresh_token, expires_in

    Raises:
        Exception: Token 交换失败
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.SECOND_ME_API_BASE_URL}/api/oauth/token/code",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.SECOND_ME_REDIRECT_URI,
                    "client_id": settings.SECOND_ME_CLIENT_ID,
                    "client_secret": settings.SECOND_ME_CLIENT_SECRET
                }
            )

            # 检查 HTTP 状态码
            response.raise_for_status()

            result = response.json()

            # 检查 Second Me API 响应码
            if result.get("code") != 0:
                error_msg = result.get("message", "Unknown error")
                error_code = result.get("errorCode", "unknown")
                raise Exception(f"{error_code}: {error_msg}")

            # 提取数据（注意：Second Me 使用 camelCase）
            data = result["data"]

            return {
                "access_token": data["accessToken"],        # 转换为 snake_case
                "refresh_token": data["refreshToken"],      # 转换为 snake_case
                "expires_in": data["expiresIn"]             # 保持一致
            }

    except httpx.HTTPError as e:
        raise Exception(f"HTTP request failed: {str(e)}")
    except Exception as e:
        raise Exception(f"Token exchange failed: {str(e)}")


async def get_user_info(access_token: str) -> Dict:
    """
    获取 Second Me 用户信息

    API 端点：
    GET /api/secondme/user/info

    响应格式：
    {
      "code": 0,
      "data": {
        "userId": "labs_user_xxx",
        "email": "user@example.com",
        "name": "用户姓名",
        "avatarUrl": "https://...",
        "route": "xxx"
      }
    }

    Args:
        access_token: Second Me Access Token

    Returns:
        Dict: 用户信息（userId, email, name, avatarUrl, route）

    Raises:
        Exception: 获取用户信息失败
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.SECOND_ME_API_BASE_URL}/api/secondme/user/info",
                headers={"Authorization": f"Bearer {access_token}"}
            )

            response.raise_for_status()
            result = response.json()

            if result.get("code") != 0:
                raise Exception("Get user info failed")

            # 返回 data 内的数据
            return result["data"]

    except httpx.HTTPError as e:
        raise Exception(f"HTTP request failed: {str(e)}")
    except Exception as e:
        raise Exception(f"Get user info failed: {str(e)}")


async def create_or_get_user(
    db: Session,
    user_info: Dict,
    tokens: Dict
) -> User:
    """
    创建或获取 SocialClaw 用户账号

    首次登录流程：
    1. 检查用户是否已存在（通过 second_me_user_id）
    2. 如果不存在，创建新用户
    3. 创建/更新 Second Me 绑定信息
    4. 返回用户对象

    已绑定用户流程：
    1. 检查用户是否存在
    2. 更新绑定信息（access_token, refresh_token）
    3. 返回用户对象

    Args:
        db: SQLAlchemy 数据库会话
        user_info: Second Me 用户信息
        tokens: Second Me Token 信息（access_token, refresh_token, expires_in）

    Returns:
        User: SocialClaw 用户对象
    """
    second_me_user_id = user_info["userId"]
    user_id = f"soc_user_{second_me_user_id}"

    # 检查用户是否存在
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        # ========== 首次登录：创建新用户 ==========
        print(f"Creating new user: {user_id}")

        user = User(
            user_id=user_id,
            second_me_user_id=second_me_user_id,
            email=user_info["email"],
            username=user_info.get("name", user_info["email"].split("@")[0]),
            avatar_url=user_info.get("avatarUrl")
        )
        db.add(user)

        # 创建 Second Me 绑定信息
        binding = SecondMeBinding(
            binding_id=f"binding_{uuid.uuid4().hex}",
            user_id=user_id,
            second_me_user_id=second_me_user_id,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_at=datetime.utcnow() + timedelta(seconds=tokens["expires_in"]),
            scope="user.info,user.info.shades,user.info.softmemory"
        )
        db.add(binding)

        db.commit()
        db.refresh(user)

        print(f"✓ New user created: {user_id}")

    else:
        # ========== 已绑定用户：更新绑定信息 ==========
        print(f"Updating existing user: {user_id}")

        binding = db.query(SecondMeBinding).filter(
            SecondMeBinding.user_id == user_id
        ).first()

        if binding:
            # 更新 Token 信息
            binding.access_token = tokens["access_token"]
            binding.refresh_token = tokens["refresh_token"]
            binding.expires_at = datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
            binding.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(user)

            print(f"✓ User binding updated: {user_id}")
        else:
            # 理论上不应该发生（用户存在但无绑定）
            raise Exception(f"User {user_id} exists but has no binding")

    return user


async def refresh_second_me_token(refresh_token: str) -> Dict:
    """
    刷新 Second Me Token

    当 Second Me Access Token 过期时（2 小时后），使用 refresh_token 换取新的 Token

    API 端点：
    POST /api/oauth/token/refresh

    响应格式：
    {
      "code": 0,
      "data": {
        "accessToken": "lba_at_new...",
        "refreshToken": "lba_rt_new...",
        "expiresIn": 7200
      }
    }

    Args:
        refresh_token: Second Me Refresh Token

    Returns:
        Dict: 包含新的 access_token, refresh_token, expires_in
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.SECOND_ME_API_BASE_URL}/api/oauth/token/refresh",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": settings.SECOND_ME_CLIENT_ID,
                    "client_secret": settings.SECOND_ME_CLIENT_SECRET
                }
            )

            response.raise_for_status()
            result = response.json()

            if result.get("code") != 0:
                raise Exception("Token refresh failed")

            data = result["data"]

            return {
                "access_token": data["accessToken"],
                "refresh_token": data["refreshToken"],
                "expires_in": data["expiresIn"]
            }

    except httpx.HTTPError as e:
        raise Exception(f"HTTP request failed: {str(e)}")
    except Exception as e:
        raise Exception(f"Token refresh failed: {str(e)}")
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_auth_service.py -v
```

Expected output:
```
PASSED tests/test_auth_service.py::TestAuthService::test_exchange_code_for_token_success
PASSED tests/test_auth_service.py::TestAuthService::test_exchange_code_for_token_failure
PASSED tests/test_auth_service.py::TestAuthService::test_get_user_info_success
PASSED tests/test_auth_service.py::TestAuthService::test_refresh_token_success
```

- [ ] **Step 5: 提交代码**

```bash
git add app/services/auth_service.py tests/test_auth_service.py
git commit -m "feat(auth): implement auth service (token exchange, user info, create user)"
```

---

## Task 3: 实现用户信息路由

**Files:**
- Create: `app/api/v1/users.py`
- Test: `tests/test_users.py`

### 3.1 创建用户信息路由测试

- [ ] **Step 1: 创建测试文件 `tests/test_users.py`**

```python
"""
用户信息路由测试
测试用例：
- 获取当前用户信息（带认证）
- 获取当前用户信息（未认证应该失败）
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app


class TestUserRoutes:
    """用户信息路由测试"""

    def test_get_current_user_info_authenticated(self):
        """测试获取当前用户信息（已认证）"""
        client = TestClient(app)

        # Mock JWT Token（实际测试需要数据库中的真实用户）
        test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx"

        with patch('app.core.auth.decode_access_token') as mock_decode:
            mock_decode.return_value = {
                "user_id": "soc_user_test123",
                "second_me_user_id": "labs_user_test123",
                "email": "user@example.com",
                "exp": 9999999999
            }

            with patch('app.core.auth.get_db') as mock_db:
                # Mock User 对象
                mock_user = MagicMock()
                mock_user.user_id = "soc_user_test123"
                mock_user.second_me_user_id = "labs_user_test123"
                mock_user.email = "user@example.com"
                mock_user.username = "测试用户"
                mock_user.avatar_url = "https://example.com/avatar.jpg"
                mock_user.created_at = None

                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_user
                mock_session = MagicMock()
                mock_session.query.return_value = mock_query
                mock_db.return_value.__enter__.return_value = mock_session

                response = client.get(
                    "/api/v1/users/me",
                    headers={"Authorization": f"Bearer {test_token}"}
                )

                assert response.status_code == 200
                data = response.json()["data"]
                assert data["user_id"] == "soc_user_test123"
                assert data["email"] == "user@example.com"
                assert data["username"] == "测试用户"

    def test_get_current_user_info_unauthenticated(self):
        """测试获取当前用户信息（未认证应该失败）"""
        client = TestClient(app)

        response = client.get("/api/v1/users/me")

        # 应该返回 403 或 401
        assert response.status_code in [401, 403]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

### 3.2 实现用户信息路由

- [ ] **Step 2: 创建 `app/api/v1/users.py`**

```python
"""
用户信息路由
提供：
- 获取当前用户信息
- （后续可扩展：更新用户信息、获取其他用户信息等）
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.auth import get_current_user
from app.models.user import User
from app.database import get_db

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息

    需要认证：在 Header 中携带 JWT Token
    Authorization: Bearer {access_token}

    Returns:
        user_id: SocialClaw 用户 ID
        second_me_user_id: Second Me 用户 ID
        email: 邮箱
        username: 用户名
        avatar_url: 头像 URL
        created_at: 创建时间
    """
    return {
        "code": 0,
        "data": {
            "user_id": current_user.user_id,
            "second_me_user_id": current_user.second_me_user_id,
            "email": current_user.email,
            "username": current_user.username,
            "avatar_url": current_user.avatar_url,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None
        }
    }


@router.get("/{user_id}")
async def get_user_info_by_id(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    通过 user_id 获取用户信息（公开信息）

    注意：只返回公开信息，不返回敏感信息（如 email）
    """
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "code": 0,
        "data": {
            "user_id": user.user_id,
            "username": user.username,
            "avatar_url": user.avatar_url
        }
    }
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_users.py -v
```

- [ ] **Step 4: 提交代码**

```bash
git add app/api/v1/users.py tests/test_users.py
git commit -m "feat(users): add user info endpoints"
```

---

## Task 4: 实现端到端集成测试

**Files:**
- Test: `tests/test_auth_integration.py`

### 4.1 创建集成测试

- [ ] **Step 1: 创建集成测试文件 `tests/test_auth_integration.py`**

```python
"""
OAuth2 认证端到端集成测试
测试完整流程：
1. 登录重定向
2. 回调处理（需要 Mock Second Me API）
3. 获取用户信息
4. 刷新 Token
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from urllib.parse import urlparse, parse_qs

from app.main import app


class TestAuthIntegration:
    """OAuth2 认证集成测试"""

    def test_complete_oauth2_flow(self):
        """测试完整的 OAuth2 授权流程"""
        client = TestClient(app)

        # ========== 步骤 1: 登录重定向 ==========
        print("Step 1: OAuth2 login redirect")
        response = client.get("/api/v1/auth/oauth2/login")
        assert response.status_code == 302

        location = response.headers["location"]
        parsed_url = urlparse(location)
        query_params = parse_qs(parsed_url.query)

        assert parsed_url.netloc == "go.second.me"
        assert "client_id" in query_params

        print(f"✓ Redirected to: {location}")

        # ========== 步骤 2: 回调处理（Mock Second Me API） ==========
        print("Step 2: OAuth2 callback with mocked Second Me API")

        # Mock Token 交换
        with patch('app.services.auth_service.exchange_code_for_token') as mock_exchange:
            mock_exchange.return_value = {
                "access_token": "lba_at_test_token",
                "refresh_token": "lba_rt_test_token",
                "expires_in": 7200
            }

            # Mock 获取用户信息
            with patch('app.services.auth_service.get_user_info') as mock_get_info:
                mock_get_info.return_value = {
                    "userId": "labs_user_test123",
                    "email": "user@example.com",
                    "name": "测试用户",
                    "avatarUrl": "https://example.com/avatar.jpg"
                }

                # Mock 数据库操作
                with patch('app.services.auth_service.create_or_get_user') as mock_create_user:
                    mock_user = MagicMock()
                    mock_user.user_id = "soc_user_labs_user_test123"
                    mock_user.second_me_user_id = "labs_user_test123"
                    mock_user.email = "user@example.com"
                    mock_user.username = "测试用户"
                    mock_user.avatar_url = "https://example.com/avatar.jpg"
                    mock_user.created_at = None

                    mock_create_user.return_value = mock_user

                    # 调用回调接口
                    response = client.get(
                        "/api/v1/auth/callback",
                        params={"code": "test_auth_code_123"}
                    )

                    assert response.status_code == 200
                    data = response.json()["data"]

                    assert data["user_info"]["user_id"] == "soc_user_labs_user_test123"
                    assert data["user_info"]["email"] == "user@example.com"
                    assert "access_token" in data

                    jwt_token = data["access_token"]
                    print(f"✓ OAuth2 callback successful, JWT token: {jwt_token[:20]}...")

        # ========== 步骤 3: 使用 JWT Token 获取用户信息 ==========
        print("Step 3: Get user info with JWT token")

        with patch('app.core.auth.decode_access_token') as mock_decode:
            mock_decode.return_value = {
                "user_id": "soc_user_labs_user_test123",
                "second_me_user_id": "labs_user_test123",
                "email": "user@example.com",
                "exp": 9999999999
            }

            with patch('app.core.auth.get_db') as mock_db:
                mock_user = MagicMock()
                mock_user.user_id = "soc_user_labs_user_test123"
                mock_user.second_me_user_id = "labs_user_test123"
                mock_user.email = "user@example.com"
                mock_user.username = "测试用户"
                mock_user.avatar_url = "https://example.com/avatar.jpg"
                mock_user.created_at = None

                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_user
                mock_session = MagicMock()
                mock_session.query.return_value = mock_query
                mock_db.return_value.__enter__.return_value = mock_session

                response = client.get(
                    "/api/v1/users/me",
                    headers={"Authorization": f"Bearer {jwt_token}"}
                )

                assert response.status_code == 200
                user_data = response.json()["data"]

                assert user_data["user_id"] == "soc_user_labs_user_test123"
                assert user_data["email"] == "user@example.com"

                print(f"✓ User info retrieved successfully")

        print("✓ Complete OAuth2 flow test passed!")

    def test_oauth2_callback_invalid_code(self):
        """测试无效授权码的错误处理"""
        client = TestClient(app)

        with patch('app.services.auth_service.exchange_code_for_token') as mock_exchange:
            mock_exchange.side_effect = Exception("Invalid authorization code")

            response = client.get(
                "/api/v1/auth/callback",
                params={"code": "invalid_code"}
            )

            assert response.status_code == 400
            assert "OAuth2 授权失败" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

- [ ] **Step 2: 运行集成测试**

```bash
pytest tests/test_auth_integration.py -v
```

Expected output:
```
PASSED tests/test_auth_integration.py::TestAuthIntegration::test_complete_oauth2_flow
PASSED tests/test_auth_integration.py::TestAuthIntegration::test_oauth2_callback_invalid_code
```

- [ ] **Step 3: 提交代码**

```bash
git add tests/test_auth_integration.py
git commit -m "test(auth): add OAuth2 end-to-end integration tests"
```

---

## Task 5: 注册路由到主应用

**Files:**
- Modify: `app/main.py`

- [ ] **Step 1: 在 `app/main.py` 中注册认证和用户路由**

```python
# 在 app/main.py 中添加路由导入
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router

# 在 app 创建后注册路由
app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
app.include_router(users_router, prefix="/api/v1", tags=["Users"])
```

- [ ] **Step 2: 验证路由是否注册成功**

```bash
# 启动应用
python -m uvicorn app.main:app --reload

# 访问文档查看路由
# http://localhost:8000/docs
```

- [ ] **Step 3: 运行所有测试**

```bash
pytest tests/test_auth_oauth2.py tests/test_auth_service.py tests/test_users.py tests/test_auth_integration.py -v
```

Expected output:
```
PASSED tests/test_auth_oauth2.py::TestOAuth2Login::test_oauth2_login_redirect
PASSED tests/test_auth_oauth2.py::TestOAuth2Login::test_oauth2_login_url_structure
PASSED tests/test_auth_service.py::TestAuthService::test_exchange_code_for_token_success
PASSED tests/test_auth_service.py::TestAuthService::test_exchange_code_for_token_failure
PASSED tests/test_auth_service.py::TestAuthService::test_get_user_info_success
PASSED tests/test_auth_service.py::TestAuthService::test_refresh_token_success
PASSED tests/test_users.py::TestUserRoutes::test_get_current_user_info_authenticated
PASSED tests/test_users.py::TestUserRoutes::test_get_current_user_info_unauthenticated
PASSED tests/test_auth_integration.py::TestAuthIntegration::test_complete_oauth2_flow
PASSED tests/test_auth_integration.py::TestAuthIntegration::test_oauth2_callback_invalid_code
```

- [ ] **Step 4: 提交最终代码**

```bash
git add app/main.py
git commit -m "feat(auth): register auth and users routes to main app"
```

---

## Task 6: 手动测试和验证

### 6.1 启动应用

- [ ] **Step 1: 启动开发服务器**

```bash
# 确保 .env 文件配置正确
python -m uvicorn app.main:app --reload --port 8000
```

### 6.2 测试 OAuth2 登录流程

- [ ] **Step 2: 访问登录页面**

```
浏览器访问: http://localhost:8000/api/v1/auth/oauth2/login

预期行为：
1. 自动重定向到 Second Me 授权页面
2. URL 应该包含正确的参数：
   - client_id=29347211-adcf-46aa-b135-128645948227
   - redirect_uri=http://localhost:8000/auth/callback
   - response_type=code
   - scope=user.info,user.info.shades,user.info.softmemory
```

### 6.3 测试回调处理（使用 Mock）

- [ ] **Step 3: 使用 cURL 测试回调（需要有效的 auth_code）**

```bash
# 实际测试需要从 Second Me 获取真实的 auth_code
# 这里使用 Mock 测试
curl -X GET "http://localhost:8000/api/v1/auth/callback?code=test_code_123" \
  -H "Content-Type: application/json"
```

预期响应：
```json
{
  "code": 0,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user_info": {
      "user_id": "soc_user_labs_user_xxx",
      "second_me_user_id": "labs_user_xxx",
      "email": "user@example.com",
      "username": "用户姓名",
      "avatar_url": "https://...",
      "created_at": "2026-03-16T..."
    }
  }
}
```

### 6.4 测试用户信息接口

- [ ] **Step 4: 使用 JWT Token 获取用户信息**

```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer {your_jwt_token}"
```

### 6.5 测试 Token 刷新

- [ ] **Step 5: 刷新 Token**

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Authorization: Bearer {your_jwt_token}"
```

---

## 完成清单

- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 路由已注册到主应用
- [ ] 手动测试 OAuth2 登录流程
- [ ] 验证数据库记录正确创建
- [ ] 检查日志输出无错误
- [ ] 更新 API 文档（如果需要）

---

## 模块一完成！

**完成时间：** 预计 4-5 小时

**已实现功能：**
- ✅ OAuth2 授权登录重定向
- ✅ OAuth2 回调处理（Token 交换、用户信息获取、用户创建/获取）
- ✅ JWT Token 生成与验证
- ✅ Token 刷新机制
- ✅ 用户信息查询接口
- ✅ 完整的单元测试和集成测试

**下一步：**
- 开始模块二：帖子与评论系统

---

**计划完成并保存到 `docs/superpowers/plans/2026-03-16-Module1-Auth-Implementation-Plan.md`。准备好开始执行了吗？**
