"""
群聊模型
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean
from datetime import datetime
from . import Base


class GroupChat(Base):
    """群聊表"""

    __tablename__ = "group_chats"

    group_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    creator_agent_id = Column(String, ForeignKey("connected_agents.agent_id"), nullable=False)
    is_public = Column(Boolean, default=True)  # 公开群组
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @property
    def created_by(self):
        """向后兼容：返回创建者ID"""
        return self.creator_agent_id
