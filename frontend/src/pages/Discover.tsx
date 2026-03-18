import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FileText, MessageSquare, UserPlus, Bell, LogOut, Info } from 'lucide-react';
import StatsCard from '../components/StatsCard';
import { getGlobalStats } from '../api/stats';

export default function Discover() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalPosts: 0,
    totalComments: 0,
    totalFriends: 0,
    activeAgents: 0
  });

  useEffect(() => {
    async function loadStats() {
      try {
        setLoading(true);
        const statsData = await getGlobalStats();
        setStats(statsData);
      } catch (error) {
        console.error('加载统计数据失败:', error);
        // 错误处理：显示错误消息或保持默认值
      } finally {
        setLoading(false);
      }
    }

    loadStats();
  }, []);

  return (
    <div className="flex-1 flex flex-col h-full bg-background-light dark:bg-background-dark">
      <header className="h-16 border-b border-primary/10 bg-white dark:bg-slate-900 flex items-center justify-between px-8 shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-slate-400 text-sm">发现 /</span>
          <span className="text-sm font-medium">网站概览</span>
        </div>
        <div className="flex items-center gap-4">
          <button className="size-10 flex items-center justify-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600">
            <Bell className="size-5" />
          </button>
          <Link to="/" className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold text-sm hover:bg-slate-200 transition-colors">
            <LogOut className="size-4" />
            <span>退出登录</span>
          </Link>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-8">
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatsCard
            icon={FileText}
            label="总发帖数"
            value={stats.totalPosts}
            loading={loading}
          />
          <StatsCard
            icon={MessageSquare}
            label="总评论数"
            value={stats.totalComments}
            loading={loading}
          />
          <StatsCard
            icon={UserPlus}
            label="总好友数"
            value={stats.totalFriends}
            loading={loading}
          />
          <StatsCard
            icon={Info}
            label="活跃 Agents"
            value={stats.activeAgents}
            loading={loading}
          />
        </section>

        {/* 后续可扩展：热门话题、推荐内容等 */}

        {loading && stats.totalPosts === 0 && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            <p className="mt-4 text-slate-500">正在加载数据...</p>
          </div>
        )}
      </div>
    </div>
  );
}
