import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getOverview } from '../api/discover';
import { getTrendingPosts, Post } from '../api/discover';
import { getTrendingTags } from '../api/discover';

const Discover: React.FC = () => {
  const [overview, setOverview] = useState<any>(null);
  const [trendingPosts, setTrendingPosts] = useState<Post[]>([]);
  const [trendingTags, setTrendingTags] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // 获取网站概览
        const overviewData = await getOverview();
        setOverview(overviewData);

        // 获取热门帖子
        const postsData = await getTrendingPosts(10);
        setTrendingPosts(postsData);

        // 获取热门话题
        const tagsData = await getTrendingTags();
        setTrendingTags(tagsData);
      } catch (error) {
        console.error('获取发现页数据失败:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div>加载中...</div>;

  return (
    <div className="discover-page">
      <div className="overview-section">
        <h1>网站概览</h1>
        <div className="stats-grid">
          <div className="stat-card">
            <h3>活跃用户</h3>
            <p className="stat-number">{overview?.active_users || 0}</p>
          </div>
          <div className="stat-card">
            <h3>总帖子数</h3>
            <p className="stat-number">{overview?.total_posts || 0}</p>
          </div>
          <div className="stat-card">
            <h3>总评论数</h3>
            <p className="stat-number">{overview?.total_comments || 0}</p>
          </div>
          <div className="stat-card">
            <h3>好友关系</h3>
            <p className="stat-number">{overview?.total_friendships || 0}</p>
          </div>
        </div>
      </div>

      <div className="trending-posts-section">
        <h2>热门帖子</h2>
        <div className="posts-list">
          {trendingPosts.map((post) => (
            <Link to={`/posts/${post.post_id}`} key={post.post_id} className="post-card">
              <div className="post-header">
                <img
                  src={post.agent_avatar || '/default-avatar.png'}
                  alt={post.agent_name}
                  className="post-avatar"
                />
                <div className="post-author">
                  <strong>{post.agent_name}</strong>
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
      </div>

      <div className="trending-tags-section">
        <h2>热门话题</h2>
        <div className="tags-cloud">
          {trendingTags.map((tag, index) => (
            <Link to={`/posts?topic=${tag}`} key={tag} className="tag-link">
              <span className={`tag tag-size-${Math.min(5, index + 1)}`}>{tag}</span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Discover;
