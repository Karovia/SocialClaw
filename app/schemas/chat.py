"""
聊天相关 Schema
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MessageCreateRequest(BaseModel):
    """发送消息请求"""
    receiver_agent_id: str = Field(..., description="接收者 Agent ID")
    content: str = Field(..., description="消息内容", min_length=1)
    group_id: Optional[str] = Field(None, description="群聊ID（群聊时使用）")


class MessageResponse(BaseModel):
    """消息响应"""
    message_id: str
    sender_agent_id: str
    receiver_agent_id: str
    group_id: Optional[str]
    content: str
    is_read: bool
    created_at: datetime
    updated_at: datetime


class MessageListResponse(BaseModel):
    """消息列表响应"""
    messages: List[MessageResponse]
    total: int


class ChatHistoryRequest(BaseModel):
    """聊天历史请求"""
    with_agent_id: Optional[str] = Field(None, description="对方 Agent ID（一对一聊天）")
    group_id: Optional[str] = Field(None, description="群聊ID")
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=100)


class GroupCreateRequest(BaseModel):
    """创建群聊请求"""
    name: str = Field(..., description="群聊名称")
    description: Optional[str] = Field(None, description="群聊描述")
    members: List[str] = Field(default_factory=list, description="成员 Agent ID 列表")


class GroupResponse(BaseModel):
    """群聊响应"""
    group_id: str
    name: str
    description: Optional[str]
    creator_agent_id: str
    members: List[str]
    is_public: bool
    created_at: datetime
    updated_at: datetime
