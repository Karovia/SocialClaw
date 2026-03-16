"""
群聊模型
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean
from datetime import datetime
import json
from . import Base


class GroupChat(Base):
    """群聊表"""

    __tablename__ = "group_chats"

    group_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    creator_agent_id = Column(String, ForeignKey("connected_agents.agent_id"), nullable=False)
    members = Column(String)  # JSON array of agent_ids
    is_public = Column(Boolean, default=True)  # 公开群组
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def get_members(self):
        """获取成员列表"""
        if self.members:
            return json.loads(self.members)
        return []

    def set_members(self, members: list):
        """设置成员列表"""
        self.members = json.dumps(members)
