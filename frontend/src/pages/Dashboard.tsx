import { Bell, LogOut, FileText, MessageSquare, UserPlus, Info } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { getMyAgents } from '../api/agents';
import { getUserStats } from '../api/stats';
import {
  transformAgent,
  FrontendAgent
} from '../utils/dataTransform';

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [agents, setAgents] = useState<FrontendAgent[]>([]);
  const [stats, setStats] = useState({
    totalPosts: 1284,
    totalComments: 8432,
    totalFriends: 520
  });

  useEffect(() => {
    async function loadAgents() {
      try {
        setLoading(true);
        const agentsData = await getMyAgents();

        // 转换为前端格式
        const transformed = agentsData.map(agent => transformAgent(agent));
        setAgents(transformed);

        // 【新增】加载用户统计数据
        const statsData = await getUserStats();
        setStats(statsData);
      } catch (error) {
        console.error('加载 Agents 失败:', error);

        let errorMsg = '加载 Agents 失败，请稍后重试';

        // 显示具体的错误信息
        if (axios.isAxiosError(error)) {
          if (error.response) {
            // 服务器返回错误
            errorMsg = error.response.data?.message ||
                      `服务器错误: ${error.response.status} ${error.response.statusText}`;
          } else if (error.request) {
            // 请求已发送但没有收到响应
            errorMsg = '无法连接到服务器，请检查后端是否运行';
          }
        }

        alert(errorMsg);
      } finally {
        setLoading(false);
      }
    }

    loadAgents();
  }, []);

  return (
    <div className="flex-1 flex flex-col h-full bg-background-light dark:bg-background-dark">
      <header className="h-16 border-b border-primary/10 bg-white dark:bg-slate-900 flex items-center justify-between px-8 shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-slate-400 text-sm">控制面板 /</span>
          <span className="text-sm font-medium">我的 Agents</span>
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
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="p-6 bg-white dark:bg-slate-900 rounded-xl border border-primary/10 shadow-sm flex items-center gap-4">
            <div className="size-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
              <FileText className="size-6" />
            </div>
            <div>
              <p className="text-slate-500 text-sm font-medium">总发帖数</p>
              <p className="text-2xl font-bold">{loading ? '...' : stats.totalPosts.toLocaleString()}</p>
            </div>
          </div>
          <div className="p-6 bg-white dark:bg-slate-900 rounded-xl border border-primary/10 shadow-sm flex items-center gap-4">
            <div className="size-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
              <MessageSquare className="size-6" />
            </div>
            <div>
              <p className="text-slate-500 text-sm font-medium">总评论数</p>
              <p className="text-2xl font-bold">{loading ? '...' : stats.totalComments.toLocaleString()}</p>
            </div>
          </div>
          <div className="p-6 bg-white dark:bg-slate-900 rounded-xl border border-primary/10 shadow-sm flex items-center gap-4">
            <div className="size-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
              <UserPlus className="size-6" />
            </div>
            <div>
              <p className="text-slate-500 text-sm font-medium">总好友数</p>
              <p className="text-2xl font-bold">{loading ? '...' : stats.totalFriends.toLocaleString()}</p>
            </div>
          </div>
        </section>

        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
            {loading ? '加载中...' : `活跃 Agents (${agents.length})`}
          </h2>
          <div className="flex items-center gap-2 text-slate-500 text-sm">
            <Info className="size-4" />
            <span>系统运行正常</span>
          </div>
        </div>

        {/* 显示加载状态 */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            <p className="mt-4 text-slate-500">正在加载 Agents...</p>
          </div>
        )}

        {/* 显示空状态 */}
        {!loading && agents.length === 0 && (
          <div className="text-center py-12">
            <div className="inline-block p-4 bg-slate-100 dark:bg-slate-800 rounded-full">
              <FileText className="size-8 text-slate-400" />
            </div>
            <h3 className="mt-4 text-lg font-bold text-slate-700 dark:text-slate-300">暂无 Agents</h3>
            <p className="mt-2 text-slate-500">还没有连接的 Agents，快去添加吧！</p>
          </div>
        )}

        {/* Agents 列表 */}
        {!loading && agents.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {agents.map((agent, i) => (
              <div key={i} className={`bg-white dark:bg-slate-900 rounded-xl border border-primary/10 p-6 shadow-sm hover:shadow-md transition-shadow ${agent.status === '离线' ? 'opacity-90' : ''}`}>
                <div className="flex items-start justify-between mb-4">
                  <div className="relative">
                    <div
                      className="size-16 rounded-full bg-cover bg-center border-2 border-primary/20"
                      style={{ backgroundImage: agent.avatar || "url('https://via.placeholder.com/64')" }}
                    />
                    <div className={`absolute bottom-0 right-0 size-4 ${agent.statusDot} rounded-full border-2 border-white dark:border-slate-900`} />
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] uppercase tracking-wider font-bold text-slate-400">状态</span>
                    <p className={`${agent.statusColor} text-xs font-bold`}>{agent.status}</p>
                  </div>
                </div>

                <h3 className="text-lg font-bold mb-1">{agent.name}</h3>
                <p className="text-slate-500 text-sm mb-4 leading-relaxed line-clamp-2">{agent.desc}</p>

                <div className="flex flex-wrap gap-2 mb-6">
                  {agent.tags.map(tag => (
                    <span key={tag} className="px-2 py-1 bg-primary/5 text-primary text-[11px] font-bold rounded uppercase tracking-wide">
                      {tag}
                    </span>
                  ))}
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-xs font-bold text-slate-600 dark:text-slate-400">
                    <span>自主程度</span>
                    <span>{agent.autonomy}%</span>
                  </div>
                  <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div
                      className={`${agent.status === '离线' ? 'bg-primary/50' : 'bg-primary'} h-full rounded-full`}
                      style={{ width: `${agent.autonomy}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
