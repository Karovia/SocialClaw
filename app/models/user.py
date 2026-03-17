"""
用户模型
"""

from sqlalchemy import Column, String, Boolean, DateTime
from datetime import datetime
from . import Base


class User(Base):
    """用户表"""

    __tablename__ = "users"

    user_id = Column(String, primary_key=True, index=True)
    second_me_user_id = Column(String, unique=True, index=True)  # Second Me 用户ID
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)  # bcrypt 哈希密码
    avatar_url = Column(String)  # 头像 URL
    has_second_me_binding = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
