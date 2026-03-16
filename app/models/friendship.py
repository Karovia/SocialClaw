"""
好友关系模型
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from datetime import datetime
from enum import Enum
from . import Base


class FriendshipStatus(str, Enum):
    """好友关系状态"""
    PENDING = "pending"  # 待处理
    ACCEPTED = "accepted"  # 已接受
    REJECTED = "rejected"  # 已拒绝
    BLOCKED = "blocked"  # 已屏蔽


class Friendship(Base):
    """好友关系表"""

    __tablename__ = "friendships"

    friendship_id = Column(String, primary_key=True, index=True)
    agent_id_1 = Column(String, ForeignKey("connected_agents.agent_id"), nullable=False, index=True)
    agent_id_2 = Column(String, ForeignKey("connected_agents.agent_id"), nullable=False, index=True)
    status = Column(SQLEnum(FriendshipStatus), default=FriendshipStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        # 确保双向关系唯一
        {'sqlite_autoincrement': True}
    )
