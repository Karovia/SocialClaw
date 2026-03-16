"""
认证相关 Schema
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str = Field(..., description="JWT 访问令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(86400, description="过期时间（秒）")
    user_info: dict = Field(..., description="用户信息")


class TokenRefreshRequest(BaseModel):
    """Token 刷新请求"""
    access_token: str = Field(..., description="当前访问令牌")


class TokenRefreshResponse(BaseModel):
    """Token 刷新响应"""
    access_token: str = Field(..., description="新的访问令牌")
    expires_in: int = Field(86400, description="过期时间（秒）")


class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    email: EmailStr = Field(..., description="邮箱")
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码", min_length=6)


class UserResponse(BaseModel):
    """用户响应"""
    user_id: str
    email: str
    username: str
    has_second_me_binding: bool
