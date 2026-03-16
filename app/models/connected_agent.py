"""
已连接的 Agent
"""

from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from datetime import datetime
import json
from . import Base


class ConnectedAgent(Base):
    """已连接的 Agent"""

    __tablename__ = "connected_agents"

    agent_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    interests = Column(String)  # JSON array
    autonomy_level = Column(String, default="80")  # 0-100
    is_active = Column(Boolean, default=True)
    last_active_at = Column(DateTime)
    connected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def get_interests(self):
        """获取兴趣列表"""
        if self.interests:
            return json.loads(self.interests)
        return []

    def set_interests(self, interests: list):
        """设置兴趣列表"""
        self.interests = json.dumps(interests)
