import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def main():
    """生成正确的 OAuth2 授权 URL"""
    print("=" * 70)
    print("OAuth2 授权配置验证")
    print("=" * 70)

    # 1. 显示当前配置
    print("\n【1】当前配置：")
    print(f"  Client ID:          {settings.SECOND_ME_CLIENT_ID}")
    print(f"  Redirect URI:       {settings.SECOND_ME_REDIRECT_URI}")
    print(f"  OAuth URL:          {settings.SECOND_ME_OAUTH_URL}")
    print(f"  API Base URL:       {settings.SECOND_ME_API_BASE_URL}")

    # 2. 验证配置
    print("\n【2】配置验证：")
    errors = []

    if not settings.SECOND_ME_CLIENT_ID:
        errors.append("[ERROR] Client ID 为空")
    else:
        print("  [OK] Client ID 已配置")

    if "localhost:8000" not in settings.SECOND_ME_REDIRECT_URI:
        errors.append("[ERROR] Redirect URI 端口错误（应该是 8000）")
    else:
        print("  [OK] Redirect URI 端口正确（8000）")

    if "/api/v1/auth/callback" not in settings.SECOND_ME_REDIRECT_URI:
        errors.append("[ERROR] Redirect URI 路径错误")
    else:
        print("  [OK] Redirect URI 路径正确")

    if settings.SECOND_ME_OAUTH_URL != "https://go.second.me/oauth/":
        errors.append("[ERROR] OAuth URL 错误")
    else:
        print("  [OK] OAuth URL 正确")

    # 3. 生成授权 URL
    print("\n【3】生成的授权 URL：")
    from urllib.parse import urlencode
    params = {
        "client_id": settings.SECOND_ME_CLIENT_ID,
        "redirect_uri": settings.SECOND_ME_REDIRECT_URI,
        "response_type": "code",
        "scope": "user.info,user.info.shades,user.info.softmemory"
    }
    auth_url = f"{settings.SECOND_ME_OAUTH_URL}?{urlencode(params)}"
    print(f"\n  {auth_url}")

    # 4. URL 解码
    print("\n【4】URL 参数解析：")
    from urllib.parse import parse_qs, urlparse
    parsed = urlparse(auth_url)
    query_params = parse_qs(parsed.query)

    print(f"  client_id:      {query_params.get('client_id', [''])[0]}")
    print(f"  redirect_uri:   {query_params.get('redirect_uri', [''])[0]}")
    print(f"  response_type:  {query_params.get('response_type', [''])[0]}")
    print(f"  scope:          {query_params.get('scope', [''])[0]}")

    # 5. Second Me 后台配置要求
    print("\n【5】Second Me 后台配置要求：")
    print("  在 Second Me 开发者后台（https://go.second.me/developer），")
    print("  找到应用（App ID: 29347211-adcf-46aa-b135-128645948227），")
    print("  将'重定向 URI'设置为：")
    print(f"\n  {settings.SECOND_ME_REDIRECT_URI}\n")

    # 6. 常见错误
    print("【6】常见错误：")
    print("  ❌ 错误的 redirect_uri: http://localhost:8080/api/v1/auth/callback")
    print("  ❌ 错误的 redirect_uri: http://localhost:3000/api/auth/callback")
    print("  ❌ 错误的 OAuth URL: https://second-me.cn/oauth")
    print("\n  ✅ 正确的 redirect_uri: http://localhost:8000/api/v1/auth/callback")
    print("  ✅ 正确的 OAuth URL: https://go.second.me/oauth/")

    # 7. 测试步骤
    print("\n【7】正确的测试步骤：")
    print("  1. 启动后端: cd D:/Socialclaw && poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000")
    print("  2. 启动前端: cd D:/Socialclaw/frontend && npm run dev")
    print("  3. 访问: http://localhost:3000/login")
    print("  4. 点击'使用 Second Me 登录'按钮")
    print("  5. 系统会自动重定向到正确的 Second Me 授权页面")
    print("  6. 在 Second Me 授权页面点击'授权'")
    print("  7. 自动回调到 SocialClaw 并登录成功")

    # 8. 错误处理
    if errors:
        print("\n【8】发现错误：")
        for error in errors:
            print(f"  {error}")
        print("\n  请修复配置文件 .env 中的相关配置")
    else:
        print("\n【8】✅ 配置检查通过！")
        print("\n  如果仍然报错，请检查 Second Me 后台的重定向 URI 配置")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
