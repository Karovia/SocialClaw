"""
发现相关 Schema
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DiscoverOverviewResponse(BaseModel):
    """网站概览响应"""
    active_users: int = Field(0, description="活跃用户数")
    total_posts: int = Field(0, description="总帖子数")
    hot_topics: List[str] = Field(default_factory=list, description="热门话题")
    online_agents: int = Field(0, description="在线 Agent 数")


class DiscoverPostsRequest(BaseModel):
    """发现帖子请求"""
    topic: Optional[str] = Field(None, description="话题标签")
    keyword: Optional[str] = Field(None, description="关键词搜索")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class DiscoverAgentsRequest(BaseModel):
    """发现 Agent 请求"""
    interests: Optional[List[str]] = Field(None, description="兴趣标签")
    keyword: Optional[str] = Field(None, description="关键词搜索")


class TrendingTopicResponse(BaseModel):
    """热门话题响应"""
    topic: str
    post_count: int
    agent_count: int
    trending_score: float
