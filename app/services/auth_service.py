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
            id=f"binding_{uuid.uuid4().hex}",
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

        print("New user created: " + user_id)

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

            print("User binding updated: " + user_id)
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
