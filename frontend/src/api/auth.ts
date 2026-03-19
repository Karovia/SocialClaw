import axios from 'axios';
import { User } from '../types/agent';

// 获取环境变量中的API基础地址
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const OAUTH_REDIRECT_URI = import.meta.env.VITE_OAUTH_REDIRECT_URI || 'http://localhost:8000/api/v1/auth/callback';

// 创建 Axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

/**
 * 获取 Token
 */
export const getToken = (): string | null => {
  return localStorage.getItem('access_token');
};

/**
 * 保存 Token
 */
export const saveToken = (token: string): void => {
  localStorage.setItem('access_token', token);
};

/**
 * 清除 Token
 */
export const clearToken = (): void => {
  localStorage.removeItem('access_token');
};

/**
 * 获取当前登录用户信息
 */
export const getCurrentUser = async (): Promise<User> => {
  const token = getToken();
  if (!token) {
    throw new Error('未登录');
  }

  try {
    const response = await api.get('/users/me', {
      headers: { Authorization: `Bearer ${token}` }
    });

    if (response.data.code === 0) {
      return response.data.data;
    }
    throw new Error(response.data.message || '获取用户信息失败');
  } catch (error) {
    clearToken();
    throw error;
  }
};

/**
 * OAuth2 登录 - 跳转到后端 OAuth2 登录端点
 */
export const oauth2Login = (): void => {
  // 跳转到后端的 OAuth2 登录端点
  // 后端会重定向到 Second Me 授权，然后回调处理，最后重定向回前端
  const loginUrl = `${API_BASE_URL.replace('/api/v1', '')}/api/v1/auth/oauth2/login`;
  window.location.href = loginUrl;
};

/**
 * OAuth2 回调 - 用 code 换取 Token
 */
export const handleOAuthCallback = async (code: string): Promise<{ access_token: string; user_info: User }> => {
  const response = await api.get('/auth/callback', {
    params: { code }
  });

  if (response.data.code === 0) {
    const { access_token, user_info } = response.data.data;
    saveToken(access_token);
    return { access_token, user_info };
  }
  throw new Error(response.data.message || 'OAuth2 授权失败');
};

/**
 * 刷新 Token
 */
export const refreshAuthToken = async (): Promise<string> => {
  const token = getToken();
  if (!token) {
    throw new Error('未登录');
  }

  const response = await api.post('/auth/refresh', null, {
    headers: { Authorization: `Bearer ${token}` }
  });

  if (response.data.code === 0) {
    const newToken = response.data.data.access_token;
    saveToken(newToken);
    return newToken;
  }
  throw new Error(response.data.message || 'Token 刷新失败');
};

/**
 * 添加请求拦截器 - 自动添加 Token
 */
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * 添加响应拦截器 - 处理 401 错误
 */
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token 过期，尝试刷新
      try {
        await refreshAuthToken();
        // 重新发送原始请求
        return api.request(error.config);
      } catch (refreshError) {
        // 刷新失败，清除 Token 并跳转到登录页
        clearToken();
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
