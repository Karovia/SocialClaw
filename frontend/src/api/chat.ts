import api from './auth';

/**
 * 获取聊天会话列表
 */
export interface ChatSession {
  session_id: string;
  session_type: 'private' | 'group';
  participants?: {
    agent_id: string;
    agent_name: string;
    agent_avatar?: string;
  }[];
  partner_id?: string;
  partner_name?: string;
  partner_avatar?: string;
  group_id?: string;
  group_name?: string;
  member_count?: number;
  last_message?: string;
  last_message_at?: string;
  unread_count: number;
}

export const getChatSessions = async (): Promise<{
  private_chats: ChatSession[];
  group_chats: ChatSession[];
}> => {
  const response = await api.get('/chat/sessions');

  if (response.data.code === 0) {
    return {
      private_chats: response.data.data.private_chats || [],
      group_chats: response.data.data.group_chats || []
    };
  }
  throw new Error(response.data.message || '获取聊天列表失败');
};

/**
 * 获取聊天历史
 */
export interface ChatMessage {
  message_id: string;
  sender_agent_id: string;
  receiver_agent_id?: string;
  group_id?: string;
  content: string;
  is_read: boolean;
  created_at: string;
}

export const getChatHistory = async (params: {
  sessionId: string;
  sessionType: 'private' | 'group';
  skip?: number;
  limit?: number;
}): Promise<ChatMessage[]> => {
  const { sessionId, sessionType, skip = 0, limit = 50 } = params;

  const response = await api.get('/chat/history', {
    params: {
      [sessionType === 'private' ? 'with_user_id' : 'group_id']: sessionId,
      skip,
      limit
    }
  });

  if (response.data.code === 0) {
    return response.data.data.messages || [];
  }
  throw new Error(response.data.message || '获取聊天历史失败');
};
