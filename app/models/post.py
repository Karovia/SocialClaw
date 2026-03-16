"""
帖子模型
"""

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean
from datetime import datetime
from . import Base


class Post(Base):
    """帖子表"""

    __tablename__ = "posts"

    post_id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("connected_agents.agent_id"), nullable=False, index=True)
    title = Column(String)
    content = Column(Text, nullable=False)
    topic = Column(String, index=True)  # 话题标签
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
