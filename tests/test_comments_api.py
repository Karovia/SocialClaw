"""
评论 API 路由测试
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


class TestCommentsAPI:
    """测试评论 API"""

    def test_create_comment_api(self, client, auth_headers):
        """测试创建评论 API"""
        # 先创建帖子
        create_resp = client.post(
            "/api/v1/posts/",
            headers=auth_headers,
            json={"content": "测试帖子", "topic": "测试"}
        )
        post_id = create_resp.json()["data"]["post_id"]

        # 创建评论
        response = client.post(
            f"/api/v1/posts/{post_id}/comments",
            headers=auth_headers,
            json={"content": "第一条评论"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["content"] == "第一条评论"
        assert data["data"]["post_id"] == post_id

    def test_create_reply_api(self, client, auth_headers):
        """测试创建回复（嵌套评论）API"""
        # 先创建帖子
        create_resp = client.post(
            "/api/v1/posts/",
            headers=auth_headers,
            json={"content": "测试帖子", "topic": "测试"}
        )
        post_id = create_resp.json()["data"]["post_id"]

        # 创建第一条评论
        comment_resp = client.post(
            f"/api/v1/posts/{post_id}/comments",
            headers=auth_headers,
            json={"content": "父评论"}
        )
        parent_comment_id = comment_resp.json()["data"]["comment_id"]

        # 创建回复
        reply_resp = client.post(
            f"/api/v1/posts/{post_id}/comments",
            headers=auth_headers,
            json={"content": "回复内容", "parent_comment_id": parent_comment_id}
        )

        assert reply_resp.status_code == 200
        data = reply_resp.json()
        assert data["data"]["content"] == "回复内容"
        assert data["data"]["parent_comment_id"] == parent_comment_id

    def test_get_comments_api(self, client, auth_headers):
        """测试获取评论列表 API"""
        # 先创建帖子
        create_resp = client.post(
            "/api/v1/posts/",
            headers=auth_headers,
            json={"content": "测试帖子", "topic": "测试"}
        )
        post_id = create_resp.json()["data"]["post_id"]

        # 创建多条评论
        client.post(f"/api/v1/posts/{post_id}/comments", headers=auth_headers,
                    json={"content": "评论 1"})
        client.post(f"/api/v1/posts/{post_id}/comments", headers=auth_headers,
                    json={"content": "评论 2"})

        # 获取评论列表
        response = client.get(f"/api/v1/posts/{post_id}/comments")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 2

    def test_delete_comment_api(self, client, auth_headers):
        """测试删除评论 API"""
        # 先创建帖子
        create_resp = client.post(
            "/api/v1/posts/",
            headers=auth_headers,
            json={"content": "测试帖子", "topic": "测试"}
        )
        post_id = create_resp.json()["data"]["post_id"]

        # 创建评论
        comment_resp = client.post(
            f"/api/v1/posts/{post_id}/comments",
            headers=auth_headers,
            json={"content": "要删除的评论"}
        )
        comment_id = comment_resp.json()["data"]["comment_id"]

        # 删除评论
        delete_resp = client.delete(
            f"/api/v1/posts/{post_id}/comments/{comment_id}",
            headers=auth_headers
        )
        assert delete_resp.status_code == 200
        assert delete_resp.json()["code"] == 0

        # 验证删除后无法获取（软删除）
        comments_resp = client.get(f"/api/v1/posts/{post_id}/comments")
        assert len(comments_resp.json()["data"]) == 0

    def test_delete_other_user_comment_api(self, client, auth_headers, db):
        """测试删除他人评论（应该失败）"""
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

        # 用其他用户创建帖子和评论
        other_post = create_post(db, other_agent.agent_id, PostCreate(content="其他用户的帖子", topic="测试"))

        # 尝试删除（应该失败）
        response = client.delete(
            f"/api/v1/posts/{other_post.post_id}/comments/nonexistent_comment",
            headers=auth_headers
        )
        assert response.status_code == 403

    def test_comment_on_nonexistent_post_api(self, client, auth_headers):
        """测试在不存在的帖子上评论（应该失败）"""
        response = client.post(
            "/api/v1/posts/post_nonexistent/comments",
            headers=auth_headers,
            json={"content": "无效评论"}
        )
        assert response.status_code == 404
