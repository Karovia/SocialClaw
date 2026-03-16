"""
Agent 相关 Schema
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AgentProfileUpdateRequest(BaseModel):
    """Agent 信息更新请求"""
    name: str = Field(..., description="Agent 名称")
    description: Optional[str] = Field(None, description="Agent 描述")
    interests: List[str] = Field(default_factory=list, description="兴趣标签列表")
    autonomy_level: str = Field("80", description="自主程度 (0-100)")


class AgentProfileResponse(BaseModel):
    """Agent 信息响应"""
    agent_id: str
    user_id: str
    name: str
    description: Optional[str]
    interests: List[str]
    autonomy_level: str
    is_active: bool
    last_active_at: Optional[datetime]
    connected_at: datetime


class AgentSearchRequest(BaseModel):
    """Agent 搜索请求"""
    interests: Optional[List[str]] = Field(None, description="兴趣标签")
    keyword: Optional[str] = Field(None, description="关键词")


class SimilarAgentResponse(BaseModel):
    """相似 Agent 响应"""
    agent_id: str
    name: str
    description: Optional[str]
    interests: List[str]
    similarity_score: float = Field(..., ge=0, le=1)
