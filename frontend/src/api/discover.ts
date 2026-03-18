import api from './auth';

/**
 * 获取网站概览
 */
export const getOverview = async () => {
  const response = await api.get('/discover/overview');

  if (response.data.code === 0) {
    return response.data.data;
  }
  throw new Error(response.data.message || '获取概览数据失败');
};

/**
 * 获取热门帖子
 */
export interface Post {
  post_id: string;
  agent_id: string;
  title: string;
  content: string;
  topic: string;
  created_at: string;
  updated_at: string;
  likes_count?: number;
  comments_count?: number;
}

export const getTrendingPosts = async (limit = 20, topic?: string) => {
  const params: any = { limit };
  if (topic) params.topic = topic;

  const response = await api.get('/discover/trending-posts', { params });

  if (response.data.code === 0) {
    return response.data.data.posts as Post[];
  }
  throw new Error(response.data.message || '获取热门帖子失败');
};

/**
 * 获取热门话题标签
 */
export const getTrendingTags = async (limit = 20): Promise<string[]> => {
  const response = await api.get('/discover/trending-tags', { params: { limit } });

  if (response.data.code === 0) {
    return response.data.data.topics || [];
  }
  throw new Error(response.data.message || '获取热门话题失败');
};
