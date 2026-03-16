"""
Second Me 绑定信息
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from datetime import datetime
from . import Base


class SecondMeBinding(Base):
    """Second Me 绑定信息"""

    __tablename__ = "second_me_bindings"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    second_me_user_id = Column(String, unique=True, index=True)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    bound_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
