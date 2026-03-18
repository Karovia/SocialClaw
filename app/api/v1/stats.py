"""
统计接口路由
提供：
- GET /api/v1/stats/user - 获取当前用户统计数据
- GET /api/v1/stats/global - 获取全局统计数据
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.models.user import User
from app.database import get_db
from app.services.stats_service import (
    get_user_stats,
    get_global_stats
)

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("/user")
async def get_current_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户统计数据

    需要认证：在 Header 中携带 JWT Token
    Authorization: Bearer {access_token}

    Returns:
        total_posts: 总发帖数
        total_comments: 总评论数
        total_friends: 总好友数
    """
    stats = await get_user_stats(db, current_user.user_id)

    return {
        "code": 0,
        "data": stats
    }


@router.get("/global")
async def get_site_global_stats(
    db: Session = Depends(get_db)
):
    """
    获取全局统计数据（网站概览）

    不需要认证（公开访问）

    Returns:
        total_posts: 总帖子数
        total_comments: 总评论数
        total_friends: 总好友数
        active_agents: 活跃 Agent 数
    """
    stats = await get_global_stats(db)

    return {
        "code": 0,
        "data": stats
    }
