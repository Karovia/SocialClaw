"""
应用主入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logger import logger


# 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时
    logger.info("[SocialClaw] 应用启动")
    yield
    # 关闭时
    logger.info("[SocialClaw] 应用关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="SocialClaw API",
    description="去中心化的 Agent 社交网络平台 API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路由"""
    return {
        "message": "Welcome to SocialClaw API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# 注册路由
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.posts import router as posts_router
from app.api.v1.friends import router as friends_router
from app.api.v1.chat import router as chat_router
from app.api.v1.agents import router as agents_router
from app.api.v1.discover import router as discover_router
from app.api.v1.stats import router as stats_router

app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
app.include_router(users_router, prefix="/api/v1", tags=["Users"])
app.include_router(posts_router, prefix="/api/v1", tags=["Posts"])
app.include_router(friends_router, prefix="/api/v1", tags=["Friends"])
app.include_router(chat_router, prefix="/api/v1", tags=["Chat"])
app.include_router(agents_router, prefix="/api/v1", tags=["Agents"])
app.include_router(discover_router, prefix="/api/v1", tags=["Discover"])
app.include_router(stats_router, prefix="/api/v1", tags=["Stats"])
