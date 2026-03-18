import api from './auth';
import { Post, Comment } from '../types/post';

/**
 * 获取帖子列表
 */
export const getPosts = async (params?: {
  topic?: string;
  skip?: number;
  limit?: number;
}): Promise<Post[]> => {
  const { topic, skip = 0, limit = 20 } = params || {};

  const response = await api.get('/posts', {
    params: { topic, skip, limit }
  });

  if (response.data.code === 0) {
    return response.data.data;
  }
  throw new Error(response.data.message || '获取帖子列表失败');
};

/**
 * 获取帖子详情
 */
export const getPostDetail = async (postId: string): Promise<Post> => {
  const response = await api.get(`/posts/${postId}`);

  if (response.data.code === 0) {
    return response.data.data;
  }
  throw new Error(response.data.message || '获取帖子详情失败');
};

/**
 * 获取评论列表
 */
export const getComments = async (postId: string): Promise<Comment[]> => {
  const response = await api.get(`/posts/${postId}/comments`);

  if (response.data.code === 0) {
    return response.data.data;
  }
  throw new Error(response.data.message || '获取评论列表失败');
};
