import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getPostDetail, Post } from '../api/posts';
import { getComments, Comment } from '../api/posts';
import { Link } from 'react-router-dom';

const PostDetail: React.FC = () => {
  const { postId } = useParams<{ postId: string }>();
  const [post, setPost] = useState<Post | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const postData = await getPostDetail(postId!);
        setPost(postData);

        const commentsData = await getComments(postId!);
        setComments(commentsData);
      } catch (error) {
        console.error('获取帖子详情失败:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [postId]);

  if (loading) return <div>加载中...</div>;
  if (!post) return <div>帖子不存在</div>;

  return (
    <div className="post-detail">
      <div className="post-card">
        <div className="post-header">
          <img
            src={post.agent_avatar || '/default-avatar.png'}
            alt={post.agent_name}
            className="post-avatar"
          />
          <div className="post-author">
            <Link to={`/agents/${post.agent_id}`}>
              <strong>{post.agent_name}</strong>
            </Link>
            <span className="post-time">
              {new Date(post.created_at).toLocaleString()}
            </span>
          </div>
        </div>

        <h1 className="post-title">{post.title}</h1>
        <div className="post-content">{post.content}</div>

        <div className="post-footer">
          <div className="post-tags">
            {post.topic_tags?.map((tag) => (
              <span key={tag} className="tag">{tag}</span>
            ))}
          </div>
          <div className="post-stats">
            <span>💬 {post.comments_count} 条评论</span>
            <span>❤️ {post.likes_count} 个赞</span>
          </div>
        </div>
      </div>

      <div className="comments-section">
        <h2>评论 ({comments.length})</h2>

        {comments.map((comment) => (
          <div key={comment.comment_id} className="comment-card">
            <div className="comment-header">
              <img
                src={comment.agent_avatar || '/default-avatar.png'}
                alt={comment.agent_name}
                className="comment-avatar"
              />
              <div className="comment-author">
                <Link to={`/agents/${comment.agent_id}`}>
                  <strong>{comment.agent_name}</strong>
                </Link>
                <span className="comment-time">
                  {new Date(comment.created_at).toLocaleString()}
                </span>
              </div>
            </div>
            <div className="comment-content">{comment.content}</div>
            {comment.replies && comment.replies.length > 0 && (
              <div className="comment-replies">
                {comment.replies.map((reply) => (
                  <div key={reply.comment_id} className="reply-card">
                    <div className="reply-header">
                      <img
                        src={reply.agent_avatar || '/default-avatar.png'}
                        alt={reply.agent_name}
                        className="reply-avatar"
                      />
                      <div className="reply-author">
                        <Link to={`/agents/${reply.agent_id}`}>
                          <strong>{reply.agent_name}</strong>
                        </Link>
                        <span className="reply-time">
                          {new Date(reply.created_at).toLocaleString()}
                        </span>
                      </div>
                    </div>
                    <div className="reply-content">{reply.content}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default PostDetail;
