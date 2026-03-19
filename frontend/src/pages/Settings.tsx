import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { LogOut, User, Mail, Shield, Settings as SettingsIcon, Users, Info, Clock } from 'lucide-react';
import { getCurrentUser, User as UserType } from '../api/auth';
import { getMyAgents, Agent } from '../api/agents';

export default function Settings() {
  const [user, setUser] = useState<UserType | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
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

  return (
    <div className="flex-1 flex flex-col h-full bg-background-light dark:bg-background-dark">
      <header className="h-16 border-b border-primary/10 bg-white dark:bg-slate-900 flex items-center justify-between px-8 shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-slate-400 text-sm">设置 /</span>
          <span className="text-sm font-medium">个人设置</span>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-4xl mx-auto">
          {/* 页面标题 */}
          <div className="flex items-center gap-3 mb-8">
            <div className="size-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
              <SettingsIcon className="size-6" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white">个人设置</h1>
              <p className="text-sm text-slate-500 mt-1">管理您的账户和 Agents 配置</p>
            </div>
          </div>

          {/* 账户信息 */}
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-primary/10 p-6 mb-6 shadow-sm">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-200 dark:border-slate-700">
              <div className="size-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                <User className="size-5" />
              </div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">账户信息</h2>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between py-3 border-b border-slate-100 dark:border-slate-800">
                <div className="flex items-center gap-3">
                  <div className="size-9 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
                    <User className="size-4 text-slate-500" />
                  </div>
                  <div>
                    <p className="text-xs text-slate-500">用户名</p>
                    <p className="text-sm font-medium text-slate-900 dark:text-white">{user?.username || '-'}</p>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between py-3 border-b border-slate-100 dark:border-slate-800">
                <div className="flex items-center gap-3">
                  <div className="size-9 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
                    <Mail className="size-4 text-slate-500" />
                  </div>
                  <div>
                    <p className="text-xs text-slate-500">邮箱地址</p>
                    <p className="text-sm font-medium text-slate-900 dark:text-white">{user?.email || '-'}</p>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between py-3 border-b border-slate-100 dark:border-slate-800">
                <div className="flex items-center gap-3">
                  <div className="size-9 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
                    <Info className="size-4 text-slate-500" />
                  </div>
                  <div>
                    <p className="text-xs text-slate-500">Second Me 用户ID</p>
                    <p className="text-sm font-medium text-slate-900 dark:text-white">{user?.second_me_user_id || '-'}</p>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between py-3">
                <div className="flex items-center gap-3">
                  <div className="size-9 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
                    <Clock className="size-4 text-slate-500" />
                  </div>
                  <div>
                    <p className="text-xs text-slate-500">注册时间</p>
                    <p className="text-sm font-medium text-slate-900 dark:text-white">
                      {user ? new Date(user.created_at).toLocaleString('zh-CN') : '-'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 我的 Agents */}
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-primary/10 p-6 mb-6 shadow-sm">
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-200 dark:border-slate-700">
              <div className="flex items-center gap-3">
                <div className="size-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                  <Users className="size-5" />
                </div>
                <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                  我的 Agents ({agents.length})
                </h2>
              </div>
            </div>

            {loading && (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            )}

            {!loading && agents.length === 0 && (
              <div className="text-center py-8">
                <p className="text-slate-500">暂无关联的 Agents</p>
              </div>
            )}

            {!loading && agents.length > 0 && (
              <div className="space-y-4">
                {agents.map((agent) => (
                  <div
                    key={agent.agent_id}
                    className="bg-slate-50 dark:bg-slate-800 rounded-lg p-4 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div
                          className="size-12 rounded-full bg-cover bg-center border-2 border-primary/20 flex-shrink-0"
                          style={{ backgroundImage: agent.avatar_url ? `url('${agent.avatar_url}')` : "url('https://via.placeholder.com/48')" }}
                        />
                        <div className="min-w-0">
                          <h3 className="text-lg font-bold text-slate-900 dark:text-white">{agent.name}</h3>
                          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1 line-clamp-2">{agent.description}</p>

                          {agent.interest_tags && agent.interest_tags.length > 0 && (
                            <div className="flex flex-wrap gap-2 mt-3">
                              {agent.interest_tags.map((tag) => (
                                <span
                                  key={tag}
                                  className="px-2 py-1 bg-primary/5 text-primary text-[10px] font-bold rounded uppercase tracking-wide"
                                >
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                      <Link
                        to={`/agents/${agent.agent_id}`}
                        className="flex items-center gap-2 px-3 py-2 bg-white dark:bg-slate-900 text-primary font-bold text-sm rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                      >
                        <span>查看详情</span>
                        <svg className="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 安全设置 */}
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-primary/10 p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-200 dark:border-slate-700">
              <div className="size-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                <Shield className="size-5" />
              </div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">安全设置</h2>
            </div>

            <div className="space-y-4">
              <button
                onClick={handleLogout}
                className="w-full flex items-center justify-center gap-3 px-6 py-4 bg-gradient-to-r from-red-500 to-red-600 text-white font-bold text-sm rounded-lg hover:from-red-600 hover:to-red-700 transition-all transform hover:scale-[1.02] shadow-md"
              >
                <LogOut className="size-5" />
                <span>退出登录</span>
              </button>

              <p className="text-xs text-slate-500 text-center mt-4">
                退出登录后，您将需要重新授权登录
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
