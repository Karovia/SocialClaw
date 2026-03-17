"""
点赞模型
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, UniqueConstraint
from datetime import datetime
from . import Base


class PostLike(Base):
    """帖子点赞表"""

    __tablename__ = "post_likes"

    id = Column(String, primary_key=True, index=True)
    post_id = Column(String, ForeignKey("posts.post_id"), nullable=False, index=True)
    agent_id = Column(String, ForeignKey("connected_agents.agent_id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 唯一约束：每个用户对每个帖子只能点赞一次
    __table_args__ = (
        UniqueConstraint('post_id', 'agent_id', name='uq_post_likes_post_agent'),
    )


class CommentLike(Base):
    """评论点赞表"""

    __tablename__ = "comment_likes"

    id = Column(String, primary_key=True, index=True)
    comment_id = Column(String, ForeignKey("comments.comment_id"), nullable=False, index=True)
    agent_id = Column(String, ForeignKey("connected_agents.agent_id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 唯一约束：每个用户对每个评论只能点赞一次
    __table_args__ = (
        UniqueConstraint('comment_id', 'agent_id', name='uq_comment_likes_comment_agent'),
    )
