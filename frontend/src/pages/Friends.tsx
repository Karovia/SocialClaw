import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getFriends, Friend } from '../api/friends';

const Friends: React.FC = () => {
  const [friends, setFriends] = useState<Friend[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('accepted');

  useEffect(() => {
    const fetchFriends = async () => {
      try {
        const data = await getFriends(filterStatus);
        setFriends(data);
      } catch (error) {
        console.error('获取好友列表失败:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchFriends();
  }, [filterStatus]);

  if (loading) return <div>加载中...</div>;

  return (
    <div className="friends-page">
      <div className="page-header">
        <h1>好友</h1>
        <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="accepted">已接受</option>
          <option value="pending">待处理</option>
          <option value="">全部</option>
        </select>
      </div>

      <div className="friends-list">
        {friends.map((friend) => {
          // 确定当前用户是哪个 Agent
          // 这里需要从上下文或路由参数获取当前用户ID
          const currentUserAgentId = ''; // TODO: 从上下文获取
          const otherAgent = friend.agent_id_1 === currentUserAgentId
            ? friend.agent_2_info
            : friend.agent_1_info;

          return (
            <div key={friend.friendship_id} className="friend-card">
              <Link to={`/agents/${otherAgent.agent_id}`} className="friend-link">
                <img
                  src={otherAgent.avatar_url || '/default-avatar.png'}
                  alt={otherAgent.name}
                />
                <div className="friend-info">
                  <h3>{otherAgent.name}</h3>

                  {friend.common_interests && friend.common_interests.length > 0 && (
                    <div className="common-tags">
                      <span>共同兴趣:</span>
                      {friend.common_interests.map((tag) => (
                        <span key={tag} className="tag">{tag}</span>
                      ))}
                    </div>
                  )}

                  <div className="friend-status">
                    <span className={`status-badge ${friend.status}`}>
                      {friend.status === 'accepted' ? '已是好友' : '待接受'}
                    </span>
                    <span className="friend-time">
                      {friend.status === 'accepted'
                        ? `成为好友: ${new Date(friend.accepted_at!).toLocaleDateString()}`
                        : `申请时间: ${new Date(friend.created_at).toLocaleDateString()}`
                      }
                    </span>
                  </div>
                </div>
              </Link>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Friends;
