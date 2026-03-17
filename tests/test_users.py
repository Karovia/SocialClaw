"""
用户信息路由测试
测试用例：
- 获取当前用户信息（带认证）
- 获取当前用户信息（未认证应该失败）
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app


class TestUserRoutes:
    """用户信息路由测试"""

    def test_get_current_user_info_authenticated(self):
        """测试获取当前用户信息（已认证）"""
        client = TestClient(app)

        # Mock JWT Token（实际测试需要数据库中的真实用户）
        test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx"

        with patch('app.core.auth.decode_access_token') as mock_decode:
            mock_decode.return_value = {
                "user_id": "soc_user_test123",
                "second_me_user_id": "labs_user_test123",
                "email": "user@example.com",
                "exp": 9999999999
            }

            with patch('app.core.auth.get_db') as mock_db:
                # Mock User 对象
                mock_user = MagicMock()
                mock_user.user_id = "soc_user_test123"
                mock_user.second_me_user_id = "labs_user_test123"
                mock_user.email = "user@example.com"
                mock_user.username = "测试用户"
                mock_user.avatar_url = "https://example.com/avatar.jpg"
                mock_user.created_at = None

                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_user
                mock_session = MagicMock()
                mock_session.query.return_value = mock_query
                mock_db.return_value.__enter__.return_value = mock_session

                response = client.get(
                    "/api/v1/users/me",
                    headers={"Authorization": f"Bearer {test_token}"}
                )

                assert response.status_code == 200
                data = response.json()["data"]
                assert data["user_id"] == "soc_user_test123"
                assert data["email"] == "user@example.com"
                assert data["username"] == "测试用户"

    def test_get_current_user_info_unauthenticated(self):
        """测试获取当前用户信息（未认证应该失败）"""
        client = TestClient(app)

        response = client.get("/api/v1/users/me")

        # 应该返回 403 或 401
        assert response.status_code in [401, 403]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
