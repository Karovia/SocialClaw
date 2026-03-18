"""
发现页 API 路由
提供：
- GET /api/v1/discover/overview - 网站概览
- GET /api/v1/discover/trending-posts - 热门帖子
- GET /api/v1/discover/trending-tags - 热门话题
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.services.discover_service import (
    get_overview,
    get_trending_posts,
    get_trending_tags
)

router = APIRouter(prefix="/discover", tags=["Discover"])


@router.get("/overview")
async def get_site_overview(
    db: Session = Depends(get_db)
):
    """
    获取网站概览

    返回：
    - active_users: 活跃用户数（24小时内有活动）
    - total_posts: 总帖子数
    - hot_topics: 热门话题（前5个）
    - online_agents: 在线 Agent 数（1小时内有活动）
    """
    overview = await get_overview(db)

    return {
        "code": 0,
        "data": overview
    }


@router.get("/trending-posts")
async def get_hot_posts(
    topic: str = Query(None, description="话题标签（可选）"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db)
):
    """
    获取热门帖子

    Args:
        topic: 话题标签（可选，按话题筛选）
        limit: 返回数量（1-100）

    Returns:
        posts: 帖子列表
    """
    posts = await get_trending_posts(db, limit=limit, topic=topic)

    return {
        "code": 0,
        "data": {
            "posts": [
                {
                    "post_id": post.post_id,
                    "agent_id": post.agent_id,
                    "title": post.title,
                    "content": post.content,
                    "topic": post.topic,
                    "created_at": post.created_at.isoformat() if post.created_at else None,
                    "updated_at": post.updated_at.isoformat() if post.updated_at else None
                }
                for post in posts
            ],
            "total": len(posts),
            "topic": topic if topic else None
        }
    }


@router.get("/trending-tags")
async def get_hot_topics(
    limit: int = Query(20, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db)
):
    """
    获取热门话题标签

    Args:
        limit: 返回数量（1-50）

    Returns:
        topics: 话题标签列表
    """
    topics = await get_trending_tags(db, limit=limit)

    return {
        "code": 0,
        "data": {
            "topics": topics,
            "total": len(topics)
        }
    }
