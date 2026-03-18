import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getCurrentUser, User } from '../api/auth';
import { getMyAgents, Agent } from '../api/agents';

const Settings: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // 获取当前用户信息
        const userData = await getCurrentUser();
        setUser(userData);

        // 获取我的 Agents
        const agentsData = await getMyAgents();
        setAgents(agentsData);
      } catch (error) {
        console.error('获取设置信息失败:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
  };

  if (loading) return <div>加载中...</div>;

  return (
    <div className="settings-page">
      <h1>个人设置</h1>

      <div className="settings-section">
        <h2>账户信息</h2>
        {user && (
          <div className="user-info">
            <div className="info-row">
              <label>用户名:</label>
              <span>{user.username}</span>
            </div>
            <div className="info-row">
              <label>邮箱:</label>
              <span>{user.email}</span>
            </div>
            <div className="info-row">
              <label>Second Me 用户ID:</label>
              <span>{user.second_me_user_id}</span>
            </div>
            <div className="info-row">
              <label>注册时间:</label>
              <span>{new Date(user.created_at).toLocaleString()}</span>
            </div>
          </div>
        )}
      </div>

      <div className="settings-section">
        <h2>我的 Agents ({agents.length})</h2>
        <div className="agents-list">
          {agents.map((agent) => (
            <div key={agent.agent_id} className="agent-item">
              <div className="agent-item-header">
                <img
                  src={agent.avatar_url || '/default-avatar.png'}
                  alt={agent.name}
                />
                <div className="agent-item-info">
                  <h3>{agent.name}</h3>
                  <p>{agent.description}</p>
                </div>
              </div>
              <div className="agent-item-actions">
                <Link to={`/agents/${agent.agent_id}`} className="btn btn-primary">
                  查看详情
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="settings-section">
        <h2>安全设置</h2>
        <button onClick={handleLogout} className="btn btn-danger">
          退出登录
        </button>
      </div>
    </div>
  );
};

export default Settings;
