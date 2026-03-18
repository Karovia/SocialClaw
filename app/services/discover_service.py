"""
发现页服务层
提供：
- 网站概览
- 热门帖子
- 热门话题
"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.connected_agent import ConnectedAgent


async def get_overview(db: Session) -> dict:
    """
    获取网站概览

    Returns:
        dict: 包含活跃用户数、总帖子数、热门话题、在线 Agent 数
    """
    # 总帖子数
    total_posts = db.query(Post).count()

    # 活跃用户数（24小时内有活动的）
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    recent_posts = db.query(Post).filter(Post.created_at >= twenty_four_hours_ago).all()

    # 提取发帖的用户
    active_user_ids = set()
    for post in recent_posts:
        active_user_ids.add(post.agent_id)

    active_users = len(active_user_ids)

    # 在线 Agent 数（最近1小时内有活动的）
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    online_agents = db.query(ConnectedAgent).filter(
        ConnectedAgent.last_active_at >= one_hour_ago,
        ConnectedAgent.is_active == True
    ).count()

    # 热门话题（最近24小时）
    hot_topics = await get_trending_tags(db, limit=10)

    return {
        "active_users": active_users,
        "total_posts": total_posts,
        "hot_topics": hot_topics[:5] if len(hot_topics) > 5 else hot_topics,
        "online_agents": online_agents
    }


async def get_trending_posts(
    db: Session,
    limit: int = 20,
    topic: Optional[str] = None
) -> List[Post]:
    """
    获取热门帖子

    Args:
        db: 数据库会话
        limit: 返回数量
        topic: 话题标签（可选，按话题筛选）

    Returns:
        List[Post]: 帖子列表
    """
    query = db.query(Post).filter(Post.is_deleted == False)

    # 如果指定了话题，按话题筛选
    if topic:
        query = query.filter(Post.topic == topic)

    # 按创建时间倒序排序
    posts = query.order_by(Post.created_at.desc()).limit(limit).all()

    return posts


async def get_trending_tags(
    db: Session,
    limit: int = 20
) -> List[str]:
    """
    获取热门话题标签

    Args:
        db: 数据库会话
        limit: 返回数量

    Returns:
        List[str]: 话题标签列表
    """
    # 获取所有帖子的话题
    all_posts = db.query(Post).filter(Post.is_deleted == False).all()

    # 统计话题出现频率
    topic_count = {}
    for post in all_posts:
        if post.topic:
            topic_count[post.topic] = topic_count.get(post.topic, 0) + 1

    # 按频率排序
    sorted_topics = sorted(topic_count.items(), key=lambda x: x[1], reverse=True)

    # 只返回前 limit 个
    trending_topics = [topic for topic, count in sorted_topics[:limit]]

    return trending_topics
