// Agent 类型定义（匹配后端响应）
export interface Agent {
  agent_id: string;
  user_id: string;
  name: string;
  description: string;
  interests: string[]; // 后端使用 interests 而不是 interest_tags
  autonomy_level: number;
  is_active: boolean;
  last_active_at: string | null;
  connected_at: string | null;
  updated_at: string | null;
  stats?: {
    posts_count: number;
    comments_count: number;
    friends_count: number;
  };
  avatar_url?: string;
  online_status?: 'online' | 'offline';
}

// 用户类型
export interface User {
  user_id: string;
  second_me_user_id: string;
  email: string;
  username: string;
  avatar_url?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
