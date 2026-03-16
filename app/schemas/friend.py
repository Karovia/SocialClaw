"""
好友相关 Schema
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class FriendshipStatusEnum(str, Enum):
    """好友关系状态枚举"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class FriendRequestRequest(BaseModel):
    """好友请求"""
    target_agent_id: str = Field(..., description="目标 Agent ID")


class FriendRequestResponse(BaseModel):
    """好友请求响应"""
    friendship_id: str
    agent_id_1: str
    agent_id_2: str
    status: FriendshipStatusEnum
    created_at: datetime
    updated_at: datetime


class FriendAcceptRequest(BaseModel):
    """接受好友请求"""
    friendship_id: str = Field(..., description="好友关系ID")


class FriendListRequest(BaseModel):
    """好友列表请求"""
    status: Optional[FriendshipStatusEnum] = Field(None, description="筛选状态")
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=100)


class FriendResponse(BaseModel):
    """好友响应"""
    agent_id: str
    name: str
    description: Optional[str]
    status: FriendshipStatusEnum
    friendship_id: str
    created_at: datetime


class FriendRecommendationResponse(BaseModel):
    """好友推荐响应"""
    agent_id: str
    name: str
    description: Optional[str]
    interests: List[str]
    match_score: float = Field(..., ge=0, le=1)
