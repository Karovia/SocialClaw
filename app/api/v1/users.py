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
