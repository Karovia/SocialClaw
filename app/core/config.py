"""
应用核心配置
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    SECRET_KEY: str = "your-secret-key-here"

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/sqlite/socialclaw.db"

    # Second Me 配置
    SECOND_ME_CLIENT_ID: str = ""
    SECOND_ME_CLIENT_SECRET: str = ""
    SECOND_ME_REDIRECT_URI: str = "http://localhost:8000/auth/callback"
    SECOND_ME_API_BASE_URL: str = "https://api.mindverse.com/gate/lab"

    # ChromaDB 配置
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma"

    # JWT 配置
    JWT_EXPIRE_HOURS: int = 24
    JWT_ALGORITHM: str = "HS256"

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"

    # Rate Limiting
    RATE_LIMIT_LOGIN_ATTEMPTS: int = 5
    RATE_LIMIT_LOGIN_PERIOD: int = 300
    RATE_LIMIT_POSTS_PER_HOUR: int = 10
    RATE_LIMIT_COMMENTS_PER_HOUR: int = 50
    RATE_LIMIT_MESSAGES_PER_HOUR: int = 100

    # Redis
    REDIS_URL: Optional[str] = "redis://localhost:6379"

    # 前端地址
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
