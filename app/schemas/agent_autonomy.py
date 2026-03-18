from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime


class AgentActionLog(BaseModel):
    """Agent 行为日志"""
    log_id: str
    agent_id: str
    user_id: str
    action_type: str
    target_id: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict] = None
    success: bool
    error_message: Optional[str] = None
    created_at: datetime


class AgentAutonomyConfig(BaseModel):
    """Agent 自主程度配置"""
    autonomy_level: int = Field(80, ge=0, le=100, description="自主程度（0-100）")
    auto_post_enabled: bool = Field(True, description="是否启用自动发帖")
    auto_friend_enabled: bool = Field(True, description="是否启用自动交友")
    post_interval_hours: int = Field(24, ge=1, description="发帖间隔（小时）")
    friend_request_limit_per_day: int = Field(5, ge=0, description="每日好友请求数上限")
    max_friends: int = Field(100, ge=0, description="最大好友数")


class GeneratePostRequest(BaseModel):
    """生成帖子请求"""
    agent_id: str
    use_memory: bool = Field(True, description="是否使用软记忆生成内容")
    max_tokens: int = Field(300, ge=50, le=1000, description="最大生成 token 数")
    topic: Optional[str] = Field(None, description="指定话题")


class GeneratePostResponse(BaseModel):
    """生成帖子响应"""
    post_id: str
    content: str
    topic: Optional[str]
    created_at: datetime