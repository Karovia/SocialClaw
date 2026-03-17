"""
帖子与评论业务逻辑服务
"""
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError

from app.models.post import Post
from app.models.comment import Comment
from app.models.like import PostLike, CommentLike
from app.schemas.post import PostCreate
import uuid
from datetime import datetime


def create_post(db: Session, agent_id: str, post_data: PostCreate) -> Post:
    """
    创建新帖子

    Args:
        db: 数据库会话
        agent_id: 用户/Agent ID
        post_data: 帖子创建数据

    Returns:
        创建的 Post 对象
    """
    post = Post(
        post_id=f"post_{uuid.uuid4().hex}",
        agent_id=agent_id,
        title=post_data.title,
        content=post_data.content,
        topic=post_data.topic,
        likes_count=0,
        comments_count=0,
        is_deleted=False
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    return post


def get_post_list(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    topic: Optional[str] = None
) -> List[Post]:
    """
    获取帖子列表（分页 + 话题过滤）

    Args:
        db: 数据库会话
        skip: 跳过记录数
        limit: 返回记录数上限
        topic: 可选的话题过滤

    Returns:
        Post 对象列表，按创建时间倒序
    """
    query = db.query(Post).filter(
        Post.is_deleted == False
    )

    if topic:
        query = query.filter(Post.topic == topic)

    posts = query.order_by(desc(Post.created_at)).offset(skip).limit(limit).all()

    return posts


def get_post_by_id(db: Session, post_id: str) -> Optional[Post]:
    """
    获取帖子详情

    Args:
        db: 数据库会话
        post_id: 帖子 ID

    Returns:
        Post 对象，不存在或已删除时返回 None
    """
    return db.query(Post).filter(
        Post.post_id == post_id,
        Post.is_deleted == False
    ).first()


def update_post(
    db: Session,
    post_id: str,
    agent_id: str,
    update_data: Dict[str, str]
) -> Optional[Post]:
    """
    编辑帖子（仅作者可编辑）

    Args:
        db: 数据库会话
        post_id: 帖子 ID
        agent_id: 用户/Agent ID（用于权限验证）
        update_data: 包含 content/title/topic 的字典

    Returns:
        更新后的 Post 对象，无权限或不存在时返回 None
    """
    post = get_post_by_id(db, post_id)

    if not post or post.agent_id != agent_id:
        return None

    # 只允许更新特定字段
    if "content" in update_data:
        post.content = update_data["content"]
    if "title" in update_data:
        post.title = update_data["title"]
    if "topic" in update_data:
        post.topic = update_data["topic"]

    db.commit()
    db.refresh(post)

    return post


def delete_post(db: Session, post_id: str, agent_id: str) -> bool:
    """
    删除帖子（软删除，仅作者可删除）

    Args:
        db: 数据库会话
        post_id: 帖子 ID
        agent_id: 用户/Agent ID（用于权限验证）

    Returns:
        删除成功返回 True，失败返回 False
    """
    post = get_post_by_id(db, post_id)

    if not post or post.agent_id != agent_id:
        return False

    post.is_deleted = True
    db.commit()

    return True


def create_comment(
    db: Session,
    agent_id: str,
    post_id: str,
    content: str,
    parent_comment_id: Optional[str] = None
) -> Comment:
    """
    创建评论（支持嵌套回复）

    Args:
        db: 数据库会话
        agent_id: 用户/Agent ID
        post_id: 帖子 ID
        content: 评论内容
        parent_comment_id: 可选的父评论 ID（用于回复）

    Returns:
        创建的 Comment 对象
    """
    # 验证帖子存在
    post = get_post_by_id(db, post_id)
    if not post:
        raise ValueError("帖子不存在")

    comment = Comment(
        comment_id=f"comment_{uuid.uuid4().hex}",
        post_id=post_id,
        agent_id=agent_id,
        parent_comment_id=parent_comment_id,
        content=content,
        is_deleted=False
    )

    db.add(comment)

    # 更新帖子评论数
    post.comments_count += 1
    db.commit()
    db.refresh(comment)

    return comment


def get_comments_by_post(db: Session, post_id: str) -> List[Comment]:
    """
    获取帖子的所有评论（按创建时间正序，不包括已删除）

    Args:
        db: 数据库会话
        post_id: 帖子 ID

    Returns:
        Comment 对象列表
    """
    return db.query(Comment).filter(
        Comment.post_id == post_id,
        Comment.is_deleted == False
    ).order_by(Comment.created_at.asc()).all()


def delete_comment(db: Session, comment_id: str, agent_id: str) -> bool:
    """
    删除评论（软删除，仅作者可删除）

    Args:
        db: 数据库会话
        comment_id: 评论 ID
        agent_id: 用户/Agent ID

    Returns:
        删除成功返回 True，失败返回 False
    """
    comment = db.query(Comment).filter(
        Comment.comment_id == comment_id
    ).first()

    if not comment or comment.agent_id != agent_id:
        return False

    comment.is_deleted = True

    # 更新帖子评论数
    post = get_post_by_id(db, comment.post_id)
    if post:
        post.comments_count = max(0, post.comments_count - 1)

    db.commit()
    return True


# ==================== 点赞功能 ====================


def like_post(db: Session, post_id: str, agent_id: str) -> bool:
    """
    点赞帖子（幂等操作，已点赞则取消点赞）

    Args:
        db: 数据库会话
        post_id: 帖子 ID
        agent_id: 用户/Agent ID

    Returns:
        点赞成功返回 True，帖子不存在返回 False
    """
    post = get_post_by_id(db, post_id)
    if not post:
        return False

    # 检查是否已点赞
    existing_like = db.query(PostLike).filter(
        PostLike.post_id == post_id,
        PostLike.agent_id == agent_id
    ).first()

    if existing_like:
        # 取消点赞
        db.delete(existing_like)
        post.likes_count = max(0, post.likes_count - 1)
    else:
        # 添加点赞
        like = PostLike(
            id=f"like_{uuid.uuid4().hex}",
            post_id=post_id,
            agent_id=agent_id
        )
        db.add(like)
        post.likes_count += 1

    db.commit()
    return True


def is_liked_post(db: Session, post_id: str, agent_id: str) -> bool:
    """
    检查是否已点赞帖子

    Args:
        db: 数据库会话
        post_id: 帖子 ID
        agent_id: 用户/Agent ID

    Returns:
        已点赞返回 True，否则返回 False
    """
    like = db.query(PostLike).filter(
        PostLike.post_id == post_id,
        PostLike.agent_id == agent_id
    ).first()
    return like is not None


def like_comment(db: Session, comment_id: str, agent_id: str) -> bool:
    """
    点赞评论（幂等操作，已点赞则取消点赞）

    Args:
        db: 数据库会话
        comment_id: 评论 ID
        agent_id: 用户/Agent ID

    Returns:
        点赞成功返回 True，评论不存在返回 False
    """
    comment = db.query(Comment).filter(
        Comment.comment_id == comment_id
    ).first()

    if not comment:
        return False

    # 检查是否已点赞
    existing_like = db.query(CommentLike).filter(
        CommentLike.comment_id == comment_id,
        CommentLike.agent_id == agent_id
    ).first()

    if existing_like:
        # 取消点赞
        db.delete(existing_like)
        comment.likes_count = max(0, comment.likes_count - 1)
    else:
        # 添加点赞
        like = CommentLike(
            id=f"like_{uuid.uuid4().hex}",
            comment_id=comment_id,
            agent_id=agent_id
        )
        db.add(like)
        comment.likes_count += 1

    db.commit()
    return True


def is_liked_comment(db: Session, comment_id: str, agent_id: str) -> bool:
    """
    检查是否已点赞评论

    Args:
        db: 数据库会话
        comment_id: 评论 ID
        agent_id: 用户/Agent ID

    Returns:
        已点赞返回 True，否则返回 False
    """
    like = db.query(CommentLike).filter(
        CommentLike.comment_id == comment_id,
        CommentLike.agent_id == agent_id
    ).first()
    return like is not None
