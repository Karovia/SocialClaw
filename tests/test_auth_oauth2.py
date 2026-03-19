"""
OAuth2 授权登录路由测试
测试用例：
- 验证登录重定向 URL 是否正确
- 验证 URL 参数是否完整（client_id, redirect_uri, response_type, scope）
"""
import pytest
from fastapi.testclient import TestClient
from urllib.parse import urlparse, parse_qs

# 导入应用（假设 app 在 app.main 中）
from app.main import app

from fastapi.testclient import TestClient


class TestOAuth2Login:
    """OAuth2 登录重定向测试"""

    def test_oauth2_login_redirect(self):
        """测试 OAuth2 登录重定向到 Second Me"""
        client = TestClient(app, follow_redirects=False)  # 禁用自动跟随重定向

        response = client.get("/api/v1/auth/oauth2/login")

        # 验证状态码（307 或 302 都是重定向）
        assert response.status_code in [302, 307], f"Expected redirect (302/307), got {response.status_code}"

        # 验证 Location header
        location = response.headers.get("location")
        assert location is not None, "Location header is missing"

        # 验证 URL 格式
        parsed_url = urlparse(location)
        assert parsed_url.netloc == "go.second.me", f"Expected go.second.me, got {parsed_url.netloc}"
        assert parsed_url.path == "/oauth/", f"Expected /oauth/, got {parsed_url.path}"

        # 验证查询参数
        query_params = parse_qs(parsed_url.query)

        # client_id 必须存在且正确
        assert "client_id" in query_params, "client_id parameter is missing"
        assert query_params["client_id"][0] == "29347211-adcf-46aa-b135-128645948227"

        # redirect_uri 必须存在
        assert "redirect_uri" in query_params, "redirect_uri parameter is missing"
        assert query_params["redirect_uri"][0] == "http://localhost:8000/api/v1/auth/callback"

        # response_type 必须是 code
        assert "response_type" in query_params, "response_type parameter is missing"
        assert query_params["response_type"][0] == "code"

        # scope 必须包含必需的权限
        assert "scope" in query_params, "scope parameter is missing"
        scopes = query_params["scope"][0].split(",")
        assert "user.info" in scopes
        assert "user.info.shades" in scopes
        assert "user.info.softmemory" in scopes

        print(f"[OK] OAuth2 login redirect URL: {location}")

    def test_oauth2_login_url_structure(self):
        """测试 OAuth2 URL 结构（不含 /authorize 等多余路径）"""
        client = TestClient(app, follow_redirects=False)  # 禁用自动跟随重定向

        response = client.get("/api/v1/auth/oauth2/login")
        location = response.headers.get("location")
        parsed_url = urlparse(location)

        # URL 必须是 https://go.second.me/oauth/?xxx 格式
        # 不能是 https://go.second.me/oauth//authorize?xxx
        assert isinstance(parsed_url.path, str), f"path should be str, got {type(parsed_url.path)}"
        assert not parsed_url.path.endswith("/authorize"), \
            "OAuth2 URL should not contain /authorize suffix"
        assert parsed_url.path == "/oauth/", \
            "OAuth2 URL path should be exactly /oauth/"

        print("[OK] OAuth2 URL structure is correct")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
