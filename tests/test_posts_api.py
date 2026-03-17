"""
帖子 API 路由测试
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="function")
def client(db):
    """测试客户端"""
    from app.database import get_db

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


class TestPostsAPI:
    """测试帖子 API"""

    def test_create_post_api(self, client, auth_headers):
        """测试创建帖子 API"""
        response = client.post(
            "/api/v1/posts/",
            headers=auth_headers,
            json={"content": "API 测试帖子", "topic": "测试"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["content"] == "API 测试帖子"
        assert data["data"]["topic"] == "测试"

    def test_get_posts_api(self, client):
        """测试获取帖子列表 API"""
        response = client.get("/api/v1/posts/")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert isinstance(data["data"], list)

    def test_get_post_detail_api(self, client, auth_headers):
        """测试获取帖子详情 API"""
        # 先创建帖子
        create_resp = client.post("/api/v1/posts/", headers=auth_headers,
                                   json={"content": "详情测试", "topic": "测试"})
        post_id = create_resp.json()["data"]["post_id"]

        # 获取详情
        response = client.get(f"/api/v1/posts/{post_id}")
        assert response.status_code == 200
        assert response.json()["data"]["content"] == "详情测试"

    def test_update_post_api(self, client, auth_headers):
        """测试编辑帖子 API"""
        # 先创建帖子
        create_resp = client.post("/api/v1/posts/", headers=auth_headers,
                                   json={"content": "原始内容", "topic": "原始"})
        post_id = create_resp.json()["data"]["post_id"]

        # 编辑帖子
        update_resp = client.put(
            f"/api/v1/posts/{post_id}",
            headers=auth_headers,
            json={"content": "更新后的内容", "topic": "更新"}
        )

        assert update_resp.status_code == 200
        assert update_resp.json()["data"]["content"] == "更新后的内容"
        assert update_resp.json()["data"]["topic"] == "更新"

    def test_delete_post_api(self, client, auth_headers):
        """测试删除帖子 API"""
        # 先创建帖子
        create_resp = client.post("/api/v1/posts/", headers=auth_headers,
                                   json={"content": "删除测试", "topic": "测试"})
        post_id = create_resp.json()["data"]["post_id"]

        # 删除
        response = client.delete(f"/api/v1/posts/{post_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["code"] == 0

        # 验证已删除
        get_resp = client.get(f"/api/v1/posts/{post_id}")
        assert get_resp.status_code == 404

    def test_delete_other_user_post_api(self, client, auth_headers, db):
        """测试删除他人帖子（应该失败）"""
        from app.models.user import User
        from app.models.connected_agent import ConnectedAgent
        from app.services.post_service import create_post
        from app.schemas.post import PostCreate

        # 创建另一个用户
        other_user = User(
            user_id="soc_user_other",
            email="other@example.com",
            username="otheruser",
            hashed_password=None,
            has_second_me_binding=True,
            is_active=True
        )
        db.add(other_user)

        other_agent = ConnectedAgent(
            agent_id="soc_user_other",
            user_id=other_user.user_id,
            name="Other Agent",
            description="Other agent"
        )
        db.add(other_agent)
        db.commit()

        # 用其他用户创建帖子
        other_post = create_post(db, other_agent.agent_id, PostCreate(content="其他用户的帖子", topic="测试"))

        # 尝试删除（应该失败）
        response = client.delete(f"/api/v1/posts/{other_post.post_id}", headers=auth_headers)
        assert response.status_code == 403
