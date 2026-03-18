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
from app.services.agent_sync_service import sync_connected_agents
from app.services.agent_autonomy_service import start_agent_autonomy
from app.core.logger import logger

router = APIRouter(tags=["Auth"])


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
    5. 生成 JWT Token 并重定向到前端

    Parameters:
    - code: Second Me 授权码（有效期 5 分钟）

    Returns:
    - 重定向到前端，携带 access_token 和 user_info
    """
    from app.services.auth_service import (
        exchange_code_for_token,
        get_user_info,
        create_or_get_user
    )
    from app.core.auth import create_access_token
    from urllib.parse import urlencode

    try:
        # 1. 用 code 换取 Second Me Token
        second_me_tokens = await exchange_code_for_token(code)

        # 2. 获取用户信息
        user_info = await get_user_info(second_me_tokens["access_token"])

        # 3. 创建或获取用户
        user = await create_or_get_user(db, user_info, second_me_tokens)

        # === 新增：同步 ConnectedAgent 信息 ===
        logger.info(f"开始同步 ConnectedAgent: {user.user_id}")
        sync_success = await sync_connected_agents(db, user.user_id, second_me_tokens["access_token"])

        if not sync_success:
            logger.warning(f"ConnectedAgent 同步失败，继续登录流程")

        # === 新增：启动定时任务 ===
        try:
            logger.info(f"启动 Agent 自主行为定时任务")
            start_agent_autonomy()
            logger.info(f"✓ Agent 自主行为定时任务已启动")
        except Exception as e:
            logger.error(f"启动 Agent 自主行为失败: {e}")

        # 4. 生成 JWT Token
        jwt_token = create_access_token(
            data={
                "user_id": user.user_id,
                "second_me_user_id": user.second_me_user_id,
                "email": user.email
            }
        )

        # 5. 构造重定向到前端的 URL，携带 Token 和用户信息
        # 注意：将敏感信息放在 URL hash 中，不会发送到服务器
        redirect_params = urlencode({
            "access_token": jwt_token,
            "user_id": user.user_id,
            "username": user.username or "",
            "avatar_url": user.avatar_url or "",
            "email": user.email or ""
        })

        frontend_url = f"{settings.FRONTEND_URL}/login?{redirect_params}"

        print(f"✓ OAuth2 callback successful for user {user.user_id}")
        print(f"✓ Redirecting to: {frontend_url}")

        return RedirectResponse(url=frontend_url)

    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ OAuth2 callback failed: {str(e)}")
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
