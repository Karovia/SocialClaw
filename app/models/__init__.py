"""
数据库模型基类
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime
from datetime import datetime


Base = declarative_base()


class BaseModel:
    """模型基类"""
    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# 导出所有模型类，方便在其他地方导入
from .user import User
from .second_me_binding import SecondMeBinding
from .connected_agent import ConnectedAgent
from .post import Post
from .comment import Comment
from .chat_message import ChatMessage
from .group_chat import GroupChat
from .group_chat_member import GroupChatMember
from .friendship import Friendship
from .activity_log import ActivityLog
from .like import PostLike, CommentLike
from .agent_autonomy_log import AgentAutonomyLog, ActionType

__all__ = [
    "Base",
    "BaseModel",
    "User",
    "SecondMeBinding",
    "ConnectedAgent",
    "Post",
    "Comment",
    "ChatMessage",
    "GroupChat",
    "GroupChatMember",
    "Friendship",
    "ActivityLog",
    "PostLike",
    "CommentLike",
    "AgentAutonomyLog",
    "ActionType"
]
