"""
基础测试
"""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_root():
    """测试根路由"""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "Welcome to SocialClaw API"


@pytest.mark.asyncio
async def test_health():
    """测试健康检查"""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
