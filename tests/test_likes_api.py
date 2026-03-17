"""
点赞功能测试
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


class TestPostLikeAPI:
    """测试帖子点赞 API"""

    def test_like_post_api(self, client, auth_headers):
        """测试点赞帖子 API"""
        # 先创建帖子
        create_resp = client.post(
            "/api/v1/posts/",
            headers=auth_headers,
            json={"content": "测试帖子", "topic": "测试"}
        )
        post_id = create_resp.json()["data"]["post_id"]

        # 点赞
        response = client.post(f"/api/v1/posts/{post_id}/like", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["is_liked"] == True

    def test_unlike_post_api(self, client, auth_headers):
        """测试取消点赞帖子 API"""
        # 先创建帖子并点赞
        create_resp = client.post(
            "/api/v1/posts/",
            headers=auth_headers,
            json={"content": "测试帖子", "topic": "测试"}
        )
        post_id = create_resp.json()["data"]["post_id"]

        # 点赞
        client.post(f"/api/v1/posts/{post_id}/like", headers=auth_headers)

        # 再次点击（取消点赞）
        response = client.post(f"/api/v1/posts/{post_id}/like", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["is_liked"] == False

    def test_get_like_status_api(self, client, auth_headers):
        """测试获取点赞状态 API"""
        # 先创建帖子
        create_resp = client.post(
            "/api/v1/posts/",
            headers=auth_headers,
            json={"content": "测试帖子", "topic": "测试"}
        )
        post_id = create_resp.json()["data"]["post_id"]

        # 未点赞状态
        status_resp = client.get(f"/api/v1/posts/{post_id}/like/status", headers=auth_headers)
        assert status_resp.json()["data"]["is_liked"] == False

        # 点赞后状态
        client.post(f"/api/v1/posts/{post_id}/like", headers=auth_headers)
        status_resp = client.get(f"/api/v1/posts/{post_id}/like/status", headers=auth_headers)
        assert status_resp.json()["data"]["is_liked"] == True

    def test_like_nonexistent_post_api(self, client, auth_headers):
        """测试点赞不存在的帖子（应该失败）"""
        response = client.post(
            "/api/v1/posts/post_nonexistent/like",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestCommentLikeAPI:
    """测试评论点赞 API"""

    def test_like_comment_api(self, client, auth_headers):
        """测试点赞评论 API"""
        # 先创建帖子和评论
        create_resp = client.post(
            "/api/v1/posts/",
            headers=auth_headers,
            json={"content": "测试帖子", "topic": "测试"}
        )
        post_id = create_resp.json()["data"]["post_id"]

        comment_resp = client.post(
            f"/api/v1/posts/{post_id}/comments",
            headers=auth_headers,
            json={"content": "测试评论"}
        )
        comment_id = comment_resp.json()["data"]["comment_id"]

        # 点赞评论
        response = client.post(
            f"/api/v1/posts/{post_id}/comments/{comment_id}/like",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["is_liked"] == True

    def test_unlike_comment_api(self, client, auth_headers):
        """测试取消点赞评论 API"""
        # 先创建帖子和评论并点赞
        create_resp = client.post(
            "/api/v1/posts/",
            headers=auth_headers,
            json={"content": "测试帖子", "topic": "测试"}
        )
        post_id = create_resp.json()["data"]["post_id"]

        comment_resp = client.post(
            f"/api/v1/posts/{post_id}/comments",
            headers=auth_headers,
            json={"content": "测试评论"}
        )
        comment_id = comment_resp.json()["data"]["comment_id"]

        # 点赞
        client.post(f"/api/v1/posts/{post_id}/comments/{comment_id}/like", headers=auth_headers)

        # 取消点赞
        response = client.post(
            f"/api/v1/posts/{post_id}/comments/{comment_id}/like",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["is_liked"] == False

    def test_like_nonexistent_comment_api(self, client, auth_headers):
        """测试点赞不存在的评论（应该失败）"""
        # 先创建帖子
        create_resp = client.post(
            "/api/v1/posts/",
            headers=auth_headers,
            json={"content": "测试帖子", "topic": "测试"}
        )
        post_id = create_resp.json()["data"]["post_id"]

        # 点赞不存在的评论
        response = client.post(
            f"/api/v1/posts/{post_id}/comments/nonexistent/like",
            headers=auth_headers
        )
        assert response.status_code == 404
