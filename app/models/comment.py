"""
评论模型
"""

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean
from datetime import datetime
from . import Base


class Comment(Base):
    """评论表"""

    __tablename__ = "comments"

    comment_id = Column(String, primary_key=True, index=True)
    post_id = Column(String, ForeignKey("posts.post_id"), nullable=False, index=True)
    agent_id = Column(String, ForeignKey("connected_agents.agent_id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    parent_comment_id = Column(String, ForeignKey("comments.comment_id"), nullable=True)  # 回复评论
    likes_count = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
