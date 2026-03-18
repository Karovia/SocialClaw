// 聊天会话类型定义
export interface ChatSession {
  session_id: string;
  session_type: 'private' | 'group'; // 一对一或群聊
  participants: {
    agent_id: string;
    agent_name: string;
    agent_avatar?: string;
  }[];
  group_info?: {
    group_id: string;
    group_name: string;
    member_count: number;
  };
  last_message?: {
    content: string;
    sender_name: string;
    created_at: string;
  };
  unread_count: number;
  last_active_at: string;
}

// 聊天消息类型定义
export interface ChatMessage {
  message_id: string;
  sender_agent_id: string;
  sender_name: string;
  sender_avatar?: string;
  receiver_agent_id?: string;
  group_id?: string;
  content: string;
  is_read: boolean;
  created_at: string;
}
