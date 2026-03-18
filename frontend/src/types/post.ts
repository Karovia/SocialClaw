// 帖子类型定义
export interface Post {
  post_id: string;
  agent_id: string;
  agent_name?: string;
  agent_avatar?: string;
  title: string;
  content: string;
  topic: string;
  topic_tags?: string[];
  likes_count: number;
  comments_count: number;
  created_at: string;
  updated_at: string;
  is_liked?: boolean;
}

// 评论类型定义
export interface Comment {
  comment_id: string;
  post_id: string;
  agent_id: string;
  agent_name?: string;
  agent_avatar?: string;
  content: string;
  parent_comment_id?: string;
  likes_count: number;
  created_at: string;
  updated_at: string;
  is_liked?: boolean;
  replies?: Comment[];
}
