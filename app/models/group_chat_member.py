"""
群聊成员关联表模型
"""
from sqlalchemy import Column, String, DateTime, ForeignKey
from datetime import datetime
from . import Base


class GroupChatMember(Base):
    """群聊成员表 - 群聊与用户的多对多关联"""

    __tablename__ = "group_chat_members"

    group_id = Column(String, ForeignKey("group_chats.group_id"), primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("connected_agents.agent_id"), primary_key=True, index=True)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
