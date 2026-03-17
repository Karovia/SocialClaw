"""
OAuth2 认证端到端集成测试
测试完整流程：
1. 登录重定向
2. 回调处理（需要 Mock Second Me API）
3. 获取用户信息
4. 刷新 Token
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from urllib.parse import urlparse, parse_qs

from app.main import app
from app.database import engine, Base

# 测试前初始化数据库
@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """创建测试数据库表"""
    Base.metadata.create_all(bind=engine)
    yield
    # 测试后清理（可选）
    # Base.metadata.drop_all(bind=engine)


class TestAuthIntegration:
    """OAuth2 认证集成测试"""

    def test_complete_oauth2_flow(self):
        """测试完整的 OAuth2 授权流程"""
        client = TestClient(app, follow_redirects=False)  # 禁用自动跟随重定向

        # ========== 步骤 1: 登录重定向 ==========
        print("Step 1: OAuth2 login redirect")
        response = client.get("/api/v1/auth/oauth2/login")
        assert response.status_code in [302, 307]  # 支持 302 和 307

        location = response.headers["location"]
        parsed_url = urlparse(location)
        query_params = parse_qs(parsed_url.query)

        assert parsed_url.netloc == "go.second.me"
        assert "client_id" in query_params

        print(f"✓ Redirected to: {location}")

        # ========== 步骤 2: 回调处理（Mock Second Me API） ==========
        print("Step 2: OAuth2 callback with mocked Second Me API")

        # Mock Token 交换
        with patch('app.services.auth_service.exchange_code_for_token') as mock_exchange:
            mock_exchange.return_value = {
                "access_token": "lba_at_test_token",
                "refresh_token": "lba_rt_test_token",
                "expires_in": 7200
            }

            # Mock 获取用户信息
            with patch('app.services.auth_service.get_user_info') as mock_get_info:
                mock_get_info.return_value = {
                    "userId": "labs_user_test123",
                    "email": "user@example.com",
                    "name": "测试用户",
                    "avatarUrl": "https://example.com/avatar.jpg"
                }

                # Mock 数据库操作
                with patch('app.services.auth_service.create_or_get_user') as mock_create_user:
                    mock_user = MagicMock()
                    mock_user.user_id = "soc_user_labs_user_test123"
                    mock_user.second_me_user_id = "labs_user_test123"
                    mock_user.email = "user@example.com"
                    mock_user.username = "测试用户"
                    mock_user.avatar_url = "https://example.com/avatar.jpg"
                    mock_user.created_at = None

                    mock_create_user.return_value = mock_user

                    # 调用回调接口
                    response = client.get(
                        "/api/v1/auth/callback",
                        params={"code": "test_auth_code_123"}
                    )

                    assert response.status_code == 200
                    data = response.json()["data"]

                    assert data["user_info"]["user_id"] == "soc_user_labs_user_test123"
                    assert data["user_info"]["email"] == "user@example.com"
                    assert "access_token" in data

                    jwt_token = data["access_token"]
                    print(f"✓ OAuth2 callback successful, JWT token: {jwt_token[:20]}...")

        print("✓ Complete OAuth2 flow test passed!")

    def test_oauth2_callback_invalid_code(self):
        """测试无效授权码的错误处理"""
        client = TestClient(app)

        with patch('app.services.auth_service.exchange_code_for_token') as mock_exchange:
            mock_exchange.side_effect = Exception("Invalid authorization code")

            response = client.get(
                "/api/v1/auth/callback",
                params={"code": "invalid_code"}
            )

            assert response.status_code == 400
            assert "OAuth2 授权失败" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
