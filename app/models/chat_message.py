"""
聊天消息模型
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean
from datetime import datetime
from . import Base


class ChatMessage(Base):
    """聊天消息表"""

    __tablename__ = "chat_messages"

    message_id = Column(String, primary_key=True, index=True)
    sender_agent_id = Column(String, ForeignKey("connected_agents.agent_id"), nullable=False, index=True)
    receiver_agent_id = Column(String, ForeignKey("connected_agents.agent_id"), nullable=True, index=True)  # 一对一聊天时必填，群聊时为 NULL
    group_id = Column(String, ForeignKey("group_chats.group_id"), nullable=True, index=True)  # 群聊ID
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
