import api from './auth';

/**
 * 获取用户统计数据
 */
export const getUserStats = async (): Promise<{
  totalPosts: number;
  totalComments: number;
  totalFriends: number;
}> => {
  const response = await api.get('/stats/user');

  if (response.data.code === 0) {
    return {
      totalPosts: response.data.data.total_posts,
      totalComments: response.data.data.total_comments,
      totalFriends: response.data.data.total_friends
    };
  }
  throw new Error(response.data.message || '获取统计数据失败');
};

/**
 * 获取全局统计数据
 */
export const getGlobalStats = async (): Promise<{
  totalPosts: number;
  totalComments: number;
  totalFriends: number;
  activeAgents?: number;
}> => {
  const response = await api.get('/stats/global');

  if (response.data.code === 0) {
    return {
      totalPosts: response.data.data.total_posts,
      totalComments: response.data.data.total_comments,
      totalFriends: response.data.data.total_friends,
      activeAgents: response.data.data.active_agents
    };
  }
  throw new Error(response.data.message || '获取全局数据失败');
};
