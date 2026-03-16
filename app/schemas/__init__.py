"""
Pydantic Schema 基类
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ResponseModel(BaseModel):
    """统一响应模型"""
    code: int = Field(0, description="状态码，0 表示成功")
    message: str = Field("成功", description="响应消息")
    data: Optional[dict] = Field(None, description="响应数据")


class TimestampMixin(BaseModel):
    """时间戳混入"""
    created_at: datetime
    updated_at: datetime
