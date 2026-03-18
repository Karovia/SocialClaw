import api from './auth';
import { Friend } from '../types/friend';

/**
 * 获取好友列表
 */
export const getFriends = async (status?: string): Promise<Friend[]> => {
  const response = await api.get('/friends', {
    params: status ? { status } : undefined
  });

  if (response.data.code === 0) {
    return response.data.data;
  }
  throw new Error(response.data.message || '获取好友列表失败');
};

/**
 * 获取推荐好友
 */
export const getRecommendations = async (limit = 10): Promise<Friend[]> => {
  const response = await api.get('/friends/recommendations', {
    params: { limit }
  });

  if (response.data.code === 0) {
    return response.data.data;
  }
  throw new Error(response.data.message || '获取推荐好友失败');
};
