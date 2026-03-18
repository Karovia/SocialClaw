// 好友类型定义
export interface Friend {
  friendship_id: string;
  agent_id_1: string;
  agent_id_2: string;
  agent_1_info: {
    agent_id: string;
    name: string;
    avatar_url?: string;
    interest_tags: string[];
  };
  agent_2_info: {
    agent_id: string;
    name: string;
    avatar_url?: string;
    interest_tags: string[];
  };
  status: 'pending' | 'accepted' | 'rejected' | 'blocked';
  common_interests?: string[];
  created_at: string;
  accepted_at?: string;
}
