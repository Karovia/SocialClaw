"""
基础测试
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """测试客户端"""
    return TestClient(app)


def test_root(client):
    """测试根路由"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to SocialClaw API"


def test_health(client):
    """测试健康检查"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
