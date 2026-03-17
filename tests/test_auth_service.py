"""
认证服务单元测试
测试用例：
- Token 交换（code -> access_token + refresh_token）
- 获取用户信息
- 创建新用户
- 获取已存在用户
- 刷新 Token
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import uuid

# Mock User 和 SecondMeBinding
class MockUser:
    def __init__(self, **kwargs):
        self.user_id = kwargs.get("user_id", "soc_user_test123")
        self.second_me_user_id = kwargs.get("second_me_user_id")
        self.email = kwargs.get("email")
        self.username = kwargs.get("username")
        self.avatar_url = kwargs.get("avatar_url")

class MockSecondMeBinding:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.user_id = kwargs.get("user_id")
        self.second_me_user_id = kwargs.get("second_me_user_id")
        self.access_token = kwargs.get("access_token")
        self.refresh_token = kwargs.get("refresh_token")
        self.expires_at = kwargs.get("expires_at")
        self.scope = kwargs.get("scope")

# 导入待测试的服务
from app.services.auth_service import (
    exchange_code_for_token,
    get_user_info,
    create_or_get_user,
    refresh_second_me_token
)


class TestAuthService:
    """认证服务测试"""

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_success(self):
        """测试用 code 成功换取 Token"""
        with patch('httpx.AsyncClient') as mock_client_class:
            # Mock HTTPX 响应
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "code": 0,
                "data": {
                    "accessToken": "lba_at_test_12345",
                    "refreshToken": "lba_rt_test_67890",
                    "tokenType": "Bearer",
                    "expiresIn": 7200
                }
            }
            mock_response.status_code = 200

            # Mock AsyncClient 实例
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()

            mock_client_class.return_value = mock_client

            # 调用服务
            result = await exchange_code_for_token("test_auth_code")

            # 验证结果
            assert result["access_token"] == "lba_at_test_12345"
            assert result["refresh_token"] == "lba_rt_test_67890"
            assert result["expires_in"] == 7200

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_failure(self):
        """测试 Token 交换失败（无效 code）"""
        # 测试 API 返回 code != 0 的情况
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "code": 1,
                "message": "Invalid authorization code",
                "errorCode": "oauth.invalid_code"
            }
            mock_response.status_code = 200

            # Mock AsyncClient 实例
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()

            mock_client_class.return_value = mock_client

            # 打印调试信息
            print("Before calling exchange_code_for_token")
            print("Mock response json:", mock_response.json.return_value)
            print("Mock client post:", mock_client.post)

            # 调用服务，应该抛出异常（code != 0）
            try:
                result = await exchange_code_for_token("invalid_code")
                print("Result:", result)
                assert False, "Should have raised an exception"
            except Exception as e:
                print("Exception caught:", str(e))
                assert "oauth.invalid_code" in str(e)

    @pytest.mark.asyncio
    async def test_get_user_info_success(self):
        """测试成功获取用户信息"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "code": 0,
                "data": {
                    "userId": "labs_user_test123",
                    "email": "user@example.com",
                    "name": "测试用户",
                    "avatarUrl": "https://example.com/avatar.jpg",
                    "route": "testuser"
                }
            }
            mock_response.status_code = 200

            # Mock AsyncClient 实例
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()

            mock_client_class.return_value = mock_client

            # 调用服务
            result = await get_user_info("lba_at_test_token")

            # 验证结果
            assert result["userId"] == "labs_user_test123"
            assert result["email"] == "user@example.com"
            assert result["name"] == "测试用户"
            assert result["avatarUrl"] == "https://example.com/avatar.jpg"

    @pytest.mark.asyncio
    async def test_refresh_token_success(self):
        """测试成功刷新 Token"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "code": 0,
                "data": {
                    "accessToken": "lba_at_new_token",
                    "refreshToken": "lba_rt_new_token",
                    "expiresIn": 7200
                }
            }
            mock_response.status_code = 200

            # Mock AsyncClient 实例
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()

            mock_client_class.return_value = mock_client

            # 调用服务
            result = await refresh_second_me_token("lba_rt_old_token")

            # 验证结果
            assert result["access_token"] == "lba_at_new_token"
            assert result["refresh_token"] == "lba_rt_new_token"
            assert result["expires_in"] == 7200

    @pytest.mark.asyncio
    async def test_create_or_get_user_new(self):
        """测试创建新用户"""
        mock_db = MagicMock()

        # Mock 第一次查询：用户不存在
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        user_info = {
            "userId": "labs_user_test123",
            "email": "user@example.com",
            "name": "测试用户",
            "avatarUrl": "https://example.com/avatar.jpg"
        }

        tokens = {
            "access_token": "lba_at_test",
            "refresh_token": "lba_rt_test",
            "expires_in": 7200
        }

        with patch('app.services.auth_service.User') as MockUser, \
             patch('app.services.auth_service.SecondMeBinding') as MockBinding:

            mock_user_instance = MagicMock()
            mock_user_instance.user_id = "soc_user_labs_user_test123"
            MockUser.return_value = mock_user_instance

            mock_binding_instance = MagicMock()
            MockBinding.return_value = mock_binding_instance

            # 替换 uuid 生成
            with patch('uuid.uuid4') as mock_uuid:
                mock_uuid.return_value.hex = "testuuid123"

                user = await create_or_get_user(mock_db, user_info, tokens)

        # 验证添加了用户和绑定
        assert mock_db.add.call_count == 2
        assert mock_db.commit.called
        assert mock_db.refresh.called

    @pytest.mark.asyncio
    async def test_create_or_get_user_existing(self):
        """测试获取已存在用户"""
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.user_id = "soc_user_test123"

        mock_query_user = MagicMock()
        mock_query_user.filter.return_value.first.return_value = mock_user
        mock_db.query.side_effect = [mock_query_user, MagicMock()]

        mock_binding = MagicMock()
        mock_query_binding = MagicMock()
        mock_query_binding.filter.return_value.first.return_value = mock_binding
        mock_db.query.side_effect = [mock_query_user, mock_query_binding]

        user_info = {
            "userId": "labs_user_test123",
            "email": "user@example.com",
            "name": "测试用户",
            "avatarUrl": "https://example.com/avatar.jpg"
        }

        tokens = {
            "access_token": "lba_at_new",
            "refresh_token": "lba_rt_new",
            "expires_in": 7200
        }

        user = await create_or_get_user(mock_db, user_info, tokens)

        # 验证更新了绑定信息
        assert mock_db.commit.called
        assert mock_binding.access_token == "lba_at_new"
        assert mock_binding.refresh_token == "lba_rt_new"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
