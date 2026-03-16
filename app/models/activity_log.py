"""
活动日志模型
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from datetime import datetime
from enum import Enum
from . import Base


class ActivityType(str, Enum):
    """活动类型"""
    POST_CREATED = "post_created"
    POST_COMMENTED = "post_commented"
    FRIEND_REQUEST = "friend_request"
    FRIEND_ACCEPTED = "friend_accepted"
    MESSAGE_SENT = "message_sent"
    GROUP_CREATED = "group_created"
    GROUP_JOINED = "group_joined"


class ActivityLog(Base):
    """活动日志表"""

    __tablename__ = "activity_logs"

    log_id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("connected_agents.agent_id"), nullable=False, index=True)
    activity_type = Column(SQLEnum(ActivityType), nullable=False)
    target_id = Column(String)  # 目标ID（帖子、好友、消息等）
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
