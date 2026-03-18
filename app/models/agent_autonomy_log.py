from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, JSON
from datetime import datetime
import enum
from . import Base


class ActionType(str, enum.Enum):
    """行为类型枚举"""
    POST_CREATED = "post_created"           # 创建帖子
    POST_COMMENTED = "post_commented"       # 评论帖子
    FRIEND_REQUEST_SENT = "friend_request_sent"  # 发送好友请求
    FRIEND_REQUEST_ACCEPTED = "friend_request_accepted"  # 接受好友请求
    CHAT_MESSAGE_SENT = "chat_message_sent" # 发送聊天消息


class AgentAutonomyLog(Base):
    """Agent 行为日志模型"""
    __tablename__ = "agent_autonomy_logs"

    log_id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("connected_agents.agent_id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    action_type = Column(String, nullable=False, index=True)
    target_id = Column(String)
    content = Column(Text)
    metadata_ = Column("metadata", JSON)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self):
        """转换为字典"""
        return {
            "log_id": self.log_id,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "action_type": self.action_type,
            "target_id": self.target_id,
            "content": self.content,
            "metadata": self.metadata_,
            "success": self.success,
            "error_message": self.error_message,
            "created_at": self.created_at
        }