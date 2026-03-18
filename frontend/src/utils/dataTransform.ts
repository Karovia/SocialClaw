/**
 * 数据转换工具
 */

// 前端 Agent 类型
export interface FrontendAgent {
  name: string;
  status: '在线' | '离线' | '离开';
  statusColor: string;
  statusDot: string;
  desc: string;
  tags: string[];
  autonomy: number;
  avatar?: string;
}

/**
 * 将后端 Agent 数据转换为前端格式
 */
export function transformAgent(agent: any): FrontendAgent {
  const autonomy = parseInt(agent.autonomy_level) || 80;
  const isActive = agent.is_active && agent.last_active_at;

  // 判断状态
  let status: '在线' | '离线' | '离开' = '离线';
  let statusColor = 'text-slate-400';
  let statusDot = 'bg-slate-300';

  if (isActive) {
    const lastActive = new Date(agent.last_active_at);
    const now = new Date();
    const diffMinutes = (now.getTime() - lastActive.getTime()) / (1000 * 60);

    if (diffMinutes < 5) {
      status = '在线';
      statusColor = 'text-primary';
      statusDot = 'bg-primary';
    } else if (diffMinutes < 30) {
      status = '离开';
      statusColor = 'text-amber-500';
      statusDot = 'bg-amber-400';
    } else {
      status = '离线';
    }
  }

  return {
    name: agent.name,
    status,
    statusColor,
    statusDot,
    desc: agent.description || '暂无描述',
    tags: Array.isArray(agent.interests) ? agent.interests : [],
    autonomy,
    avatar: agent.avatar_url || undefined
  };
}

// 前端帖子类型
export interface FrontendPost {
  name: string;
  handle: string;
  time: string;
  verified: boolean;
  content: string;
  tags?: string[];
  likes: string;
  comments: string;
  views?: string;
  avatar?: string;
  image?: string;
}

/**
 * 将后端帖子数据转换为前端格式
 */
export function transformPost(post: any): FrontendPost {
  // 计算时间差
  const now = new Date();
  const createdAt = new Date(post.created_at);
  const diffMinutes = Math.floor((now.getTime() - createdAt.getTime()) / (1000 * 60));

  let timeText = '刚刚';
  if (diffMinutes < 60) {
    timeText = `${diffMinutes}分钟前`;
  } else if (diffMinutes < 1440) {
    const hours = Math.floor(diffMinutes / 60);
    timeText = `${hours}小时前`;
  } else {
    const days = Math.floor(diffMinutes / 1440);
    timeText = `${days}天前`;
  }

  // 格式化数字
  const formatNumber = (num: number): string => {
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'k';
    }
    return num.toString();
  };

  // 后端没有 views_count，使用评论数的10倍作为预估浏览量
  const estimatedViews = (post.comments_count || 0) * 10 + (post.likes_count || 0) * 5;

  return {
    name: post.agent_name || '匿名 Agent',
    handle: `@${(post.agent_name || 'agent').toLowerCase().replace(/\s+/g, '_')}`,
    time: timeText,
    verified: true, // 默认所有帖子都已验证
    content: post.content || '',
    tags: post.topic_tags || (post.topic ? [post.topic] : []),
    likes: formatNumber(post.likes_count || 0),
    comments: formatNumber(post.comments_count || 0),
    views: formatNumber(estimatedViews),
    avatar: post.agent_avatar || undefined
  };
}

// 前端聊天会话类型
export interface FrontendChatSession {
  name: string;
  time: string;
  lastMessage: string;
  active: boolean;
  avatar?: string;
  partner_id?: string;
  group_id?: string;
}

/**
 * 将后端聊天会话数据转换为前端格式
 */
export function transformChatSession(session: any): FrontendChatSession {
  const now = new Date();
  const lastMessageAt = session.last_message_at ? new Date(session.last_message_at) : null;

  let timeText = '刚刚';
  if (lastMessageAt) {
    const diffMinutes = Math.floor((now.getTime() - lastMessageAt.getTime()) / (1000 * 60));

    if (diffMinutes < 60) {
      timeText = `${diffMinutes}分钟前`;
    } else if (diffMinutes < 1440) {
      const hours = Math.floor(diffMinutes / 60);
      timeText = `${hours}小时前`;
    } else {
      const days = Math.floor(diffMinutes / 1440);
      timeText = `${days}天前`;
    }
  }

  return {
    name: session.partner_name || session.group_name || '未知会话',
    time: timeText,
    lastMessage: session.last_message || '暂无消息',
    active: session.unread_count > 0,
    avatar: session.partner_avatar || undefined,
    partner_id: session.partner_id,
    group_id: session.group_id
  };
}
