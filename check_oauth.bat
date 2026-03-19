# 运行此脚本验证 OAuth2 配置

echo "======================================"
echo "OAuth2 配置验证"
echo "======================================"
echo ""

echo "【1】检查后端配置..."
cd /d D:/Socialclaw
poetry run python -c "from app.core.config import settings; print('✓ Redirect URI:', settings.SECOND_ME_REDIRECT_URI)"
echo ""

echo "【2】检查前端配置..."
cd /d D:/Socialclaw/frontend
cat .env | findstr "VITE_OAUTH_REDIRECT_URI"
echo ""

echo "【3】检查后端是否运行..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8000/api/v1/auth/oauth2/login
echo ""

echo "【4】检查前端是否运行..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:3000/login
echo ""

echo "【5】测试 OAuth2 登录端点..."
echo "访问: http://localhost:8000/api/v1/auth/oauth2/login"
echo "应该自动重定向到 Second Me 授权页面"
echo ""
echo "重定向地址应该是："
echo "https://go.second.me/oauth/?client_id=29347211-adcf-46aa-b135-128645948227&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fapi%2Fv1%2Fauth%2Fcallback&..."
echo ""
echo "✅ 正确的 redirect_uri: http://localhost:8000/api/v1/auth/callback"
echo "❌ 错误的 redirect_uri: http://localhost:8080/api/v1/auth/callback"
echo ""

echo "【6】下一步："
echo "1. 确保后端运行在 8000 端口"
echo "2. 确保前端运行在 3000 端口"
echo "3. 清除浏览器缓存"
echo "4. 访问 http://localhost:3000/login"
echo "5. 点击'使用 Second Me 登录'按钮"
echo "======================================"
