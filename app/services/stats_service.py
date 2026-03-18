"""
统计服务层
提供用户和全局统计数据
"""
from typing import Dict
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.post import Post
from app.models.comment import Comment
from app.models.friendship import Friendship
from app.models.connected_agent import ConnectedAgent


async def get_user_stats(db: Session, user_id: str) -> Dict:
    """
    获取当前用户的统计数据

    Args:
        db: 数据库会话
        user_id: 用户ID

    Returns:
        dict: 包含总发帖数、总评论数、总好友数
    """
    # 统计用户的帖子数
    total_posts = db.query(Post).filter(
        Post.author_id == user_id,
        Post.is_deleted == False
    ).count()

    # 统计用户的评论数
    total_comments = db.query(Comment).filter(
        Comment.author_id == user_id,
        Comment.is_deleted == False
    ).count()

    # 统计用户的好友数
    total_friends = db.query(Friendship).filter(
        ((Friendship.user_id == user_id) | (Friendship.friend_id == user_id)),
        Friendship.status == 'accepted'
    ).count()

    return {
        "total_posts": total_posts,
        "total_comments": total_comments,
        "total_friends": total_friends
    }


async def get_global_stats(db: Session) -> Dict:
    """
    获取全局统计数据

    Args:
        db: 数据库会话

    Returns:
        dict: 包含全局统计数据
    """
    # 统计总帖子数
    total_posts = db.query(Post).filter(Post.is_deleted == False).count()

    # 统计总评论数
    total_comments = db.query(Comment).filter(Comment.is_deleted == False).count()

    # 统计总好友关系数
    total_friends = db.query(Friendship).filter(
        Friendship.status == 'accepted'
    ).count()

    # 统计活跃 Agent 数（最近24小时内有活动）
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)

    active_agents = db.query(ConnectedAgent).filter(
        ConnectedAgent.is_active == True,
        ConnectedAgent.last_active_at >= twenty_four_hours_ago
    ).count()

    return {
        "total_posts": total_posts,
        "total_comments": total_comments,
        "total_friends": total_friends,
        "active_agents": active_agents
    }
