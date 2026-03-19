"""
测试 OAuth2 配置是否正确
"""
from app.core.config import settings
import urllib.parse

print("=" * 60)
print("OAuth2 配置检查")
print("=" * 60)

# 检查关键配置
print(f"\n1. Client ID: {settings.SECOND_ME_CLIENT_ID}")
print(f"   长度: {len(settings.SECOND_ME_CLIENT_ID)}")
print(f"   是否为空: {not settings.SECOND_ME_CLIENT_ID}")

print(f"\n2. Client Secret: {settings.SECOND_ME_CLIENT_SECRET[:10]}...")
print(f"   长度: {len(settings.SECOND_ME_CLIENT_SECRET)}")
print(f"   是否为空: {not settings.SECOND_ME_CLIENT_SECRET}")

print(f"\n3. Redirect URI: {settings.SECOND_ME_REDIRECT_URI}")

print(f"\n4. OAuth URL: {settings.SECOND_ME_OAUTH_URL}")

# 构造授权 URL
params = {
    "client_id": settings.SECOND_ME_CLIENT_ID,
    "redirect_uri": settings.SECOND_ME_REDIRECT_URI,
    "response_type": "code",
    "scope": "user.info,user.info.shades,user.info.softmemory"
}

auth_url = f"{settings.SECOND_ME_OAUTH_URL}?{urllib.parse.urlencode(params)}"
print(f"\n5. 完整的授权 URL:")
print(f"   {auth_url}")

print("\n" + "=" * 60)
print("请检查：")
print("1. Client ID 和 Secret 是否为空")
print("2. Redirect URI 是否与 Second Me 开发者平台完全一致")
print("3. 尝试直接在浏览器中访问上面的授权 URL")
print("=" * 60)
