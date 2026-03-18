import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getChatSessions, ChatSession } from '../api/chat';
import { getChatHistory, ChatMessage } from '../api/chat';

const ChatDetail: React.FC = () => {
  const { chatId } = useParams<{ chatId: string }>();
  const [session, setSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // 获取所有会话
        const sessions = await getChatSessions();
        const currentSession = sessions.find(s => s.session_id === chatId);
        setSession(currentSession || null);

        if (currentSession) {
          // 获取聊天历史
          const messagesData = await getChatHistory({
            sessionId: chatId,
            sessionType: currentSession.session_type
          });
          setMessages(messagesData);
        }
      } catch (error) {
        console.error('获取聊天详情失败:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [chatId]);

  if (loading) return <div>加载中...</div>;
  if (!session) return <div>聊天不存在</div>;

  return (
    <div className="chat-detail">
      <div className="chat-header">
        <h1>
          {session.session_type === 'private'
            ? session.participants[1]?.agent_name || '未知用户'
            : session.group_info?.group_name}
        </h1>
        <div className="chat-meta">
          <span>
            {session.session_type === 'private'
              ? `一对一聊天`
              : `群聊 (${session.group_info?.member_count} 人)`}
          </span>
        </div>
      </div>

      <div className="chat-messages">
        {messages.map((message) => (
          <div key={message.message_id} className="message-item">
            <div className="message-header">
              <img
                src={message.sender_avatar || '/default-avatar.png'}
                alt={message.sender_name}
                className="message-avatar"
              />
              <div className="message-meta">
                <strong>{message.sender_name}</strong>
                <span className="message-time">
                  {new Date(message.created_at).toLocaleString()}
                </span>
              </div>
            </div>
            <div className="message-content">{message.content}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ChatDetail;
