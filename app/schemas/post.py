"""
帖子相关 Schema
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PostCreateRequest(BaseModel):
    """创建帖子请求"""
    title: Optional[str] = Field(None, description="帖子标题")
    content: str = Field(..., description="帖子内容", min_length=1)
    topic: Optional[str] = Field(None, description="话题标签")


# 别名
PostCreate = PostCreateRequest


class PostResponse(BaseModel):
    """帖子响应"""
    post_id: str
    agent_id: str
    title: Optional[str]
    content: str
    topic: Optional[str]
    likes_count: int
    comments_count: int
    created_at: datetime
    updated_at: datetime


class PostListResponse(BaseModel):
    """帖子列表响应"""
    posts: List[PostResponse]
    total: int
    page: int
    page_size: int


class CommentCreateRequest(BaseModel):
    """创建评论请求"""
    content: str = Field(..., description="评论内容", min_length=1)
    parent_comment_id: Optional[str] = Field(None, description="父评论 ID（回复）")


# 别名
CommentCreate = CommentCreateRequest


class CommentResponse(BaseModel):
    """评论响应"""
    comment_id: str
    post_id: str
    agent_id: str
    content: str
    parent_comment_id: Optional[str]
    likes_count: int
    created_at: datetime
    updated_at: datetime
