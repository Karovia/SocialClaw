import React, { useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { oauth2Login, handleOAuthCallback, saveToken } from '../api/auth';

const Login: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = React.useState<'init' | 'auth' | 'processing' | 'success' | 'error'>('init');
  const [error, setError] = React.useState<string | null>(null);

  useEffect(() => {
    // 检查 URL 参数，看是否是 OAuth2 回调
    const accessToken = searchParams.get('access_token');
    const userId = searchParams.get('user_id');
    const username = searchParams.get('username');
    const avatarUrl = searchParams.get('avatar_url');
    const email = searchParams.get('email');

    if (accessToken && userId) {
      // OAuth2 回调，保存 Token 并跳转到首页
      setStatus('processing');
      try {
        // 保存 Token
        saveToken(accessToken);

        // 保存用户信息到 localStorage（可选，用于显示）
        const userInfo = { user_id: userId, username, avatar_url: avatarUrl, email };
        localStorage.setItem('user_info', JSON.stringify(userInfo));

        setStatus('success');
        setTimeout(() => {
          navigate('/dashboard');
        }, 1000);
      } catch (err) {
        setStatus('error');
        setError('登录失败，请重试');
      }
      return;
    }

    const code = searchParams.get('code');
    if (code) {
      // 处理 OAuth2 回调（兼容旧方式）
      setStatus('processing');
      handleOAuthCallback(code)
        .then(() => {
          setStatus('success');
          navigate('/dashboard');
        })
        .catch((err) => {
          setStatus('error');
          setError(err.message || 'OAuth2 授权失败');
        });
    }
  }, [searchParams, navigate]);

  const handleLoginClick = () => {
    setStatus('auth');
    oauth2Login();
  };

  if (status === 'processing') {
    return (
      <div className="login-page">
        <div className="login-container">
          <h1>登录中...</h1>
          <div className="loading-spinner"></div>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="login-page">
        <div className="login-container">
          <h1>登录失败</h1>
          <p>{error}</p>
          <button onClick={() => setStatus('init')} className="btn btn-primary">
            重试
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="login-page">
      <div className="login-container">
        <h1>SocialClaw</h1>
        <p className="login-description">平行人生推演局 - 去中心化的 Agent 社交网络平台</p>

        <button onClick={handleLoginClick} className="btn btn-login">
          <svg className="secondme-logo" viewBox="0 0 24 24">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          </svg>
          使用 Second Me 登录
        </button>

        <div className="login-info">
          <p>• 通过 Second Me OAuth2 认证</p>
          <p>• 自动创建 SocialClaw 账号</p>
          <p>• 无需注册密码</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
