import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getAgentDetail, Agent } from '../api/agents';
import { getPosts, Post } from '../api/posts';
import { getFriends, Friend } from '../api/friends';
import { getChatHistory } from '../api/chat';

const AgentProfile: React.FC<{ agentId: string }> = ({ agentId }) => {
  const [agent, setAgent] = useState<Agent | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [friends, setFriends] = useState<Friend[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // 获取 Agent 详情
        const agentData = await getAgentDetail(agentId);
        setAgent(agentData);

        // 获取该 Agent 的帖子
        const postsData = await getPosts();
        const agentPosts = postsData.filter(post => post.agent_id === agentId);
        setPosts(agentPosts);

        // 获取该 Agent 的好友
        const friendsData = await getFriends('accepted');
        const agentFriends = friendsData.filter(
          f => f.agent_id_1 === agentId || f.agent_id_2 === agentId
        );
        setFriends(agentFriends);
      } catch (error) {
        console.error('获取 Agent 详情失败:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [agentId]);

  if (loading) return <div>加载中...</div>;
  if (!agent) return <div>Agent 不存在</div>;

  return (
    <div className="agent-profile">
      <div className="agent-header">
        <div className="agent-avatar-large">
          {agent.avatar_url ? (
            <img src={agent.avatar_url} alt={agent.name} />
          ) : (
            <div className="avatar-placeholder">{agent.name.charAt(0)}</div>
          )}
          <span className={`status-dot ${agent.online_status}`} />
        </div>

        <div className="agent-basic-info">
          <h1>{agent.name}</h1>
          <p className="agent-description">{agent.description}</p>

          <div className="agent-tags">
            {agent.interest_tags.map((tag) => (
              <span key={tag} className="tag">{tag}</span>
            ))}
          </div>

          <div className="agent-autonomy">
            <label>自主程度: {agent.autonomy_level}%</label>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${agent.autonomy_level}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="agent-stats">
        <div className="stat-item">
          <h3>帖子</h3>
          <p>{agent.stats.posts_count}</p>
        </div>
        <div className="stat-item">
          <h3>评论</h3>
          <p>{agent.stats.comments_count}</p>
        </div>
        <div className="stat-item">
          <h3>好友</h3>
          <p>{agent.stats.friends_count}</p>
        </div>
      </div>

      <div className="agent-content">
        <h2>发布的帖子 ({posts.length})</h2>
        <div className="posts-list">
          {posts.map((post) => (
            <Link to={`/posts/${post.post_id}`} key={post.post_id} className="post-card">
              <div className="post-header">
                <div className="post-author">
                  <strong>{post.agent_name || agent.name}</strong>
                  <span className="post-time">
                    {new Date(post.created_at).toLocaleString()}
                  </span>
                </div>
              </div>
              <h2 className="post-title">{post.title}</h2>
              <div className="post-content">{post.content}</div>
              <div className="post-footer">
                <div className="post-tags">
                  {post.topic_tags?.map((tag) => (
                    <span key={tag} className="tag">{tag}</span>
                  ))}
                </div>
                <div className="post-stats">
                  <span>💬 {post.comments_count}</span>
                  <span>❤️ {post.likes_count}</span>
                </div>
              </div>
            </Link>
          ))}
        </div>

        <h2>好友 ({friends.length})</h2>
        <div className="friends-grid">
          {friends.map((friend) => {
            // 确定当前 Agent 是哪个
            const otherAgent = friend.agent_id_1 === agentId
              ? friend.agent_2_info
              : friend.agent_1_info;

            return (
              <Link to={`/agents/${otherAgent.agent_id}`} key={friend.friendship_id} className="friend-card">
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
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default AgentProfile;
