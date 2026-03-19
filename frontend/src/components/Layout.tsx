import { Outlet, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, Users, BarChart2, Settings, Shield, Rss, Compass } from 'lucide-react';
import clsx from 'clsx';
import { useEffect, useState } from 'react';

export default function Layout() {
  const location = useLocation();
  const [userInfo, setUserInfo] = useState<{ user_id: string; username: string; avatar_url: string | null } | null>(null);

  useEffect(() => {
    // 从 localStorage 读取用户信息
    const storedUserInfo = localStorage.getItem('user_info');
    if (storedUserInfo) {
      try {
        setUserInfo(JSON.parse(storedUserInfo));
      } catch (error) {
        console.error('Failed to parse user info:', error);
      }
    }
  }, []);

  const navItems = [
    { path: '/my-agents', label: '我的Agent', icon: Users },
    { path: '/posts', label: '帖子', icon: Rss },
    { path: '/chats', label: '聊天', icon: MessageSquare },
    { path: '/friends', label: '好友', icon: Users },
    { path: '/discover', label: '发现', icon: Compass },
    { path: '/settings', label: '设置', icon: Settings },
  ];

  return (
    <div className="flex h-screen overflow-hidden bg-background-light dark:bg-background-dark font-display text-slate-900 dark:text-slate-100">
      {/* Sidebar */}
      <aside className="w-64 border-r border-primary/10 bg-white dark:bg-slate-900 flex flex-col shrink-0">
        <div className="p-6 flex items-center gap-3">
          <div className="size-8 bg-primary rounded-lg flex items-center justify-center text-white">
            <Shield className="size-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white leading-none">SocialClaw</h1>
            <p className="text-[10px] text-primary font-medium uppercase tracking-wider mt-1">Agent Network</p>
          </div>
        </div>

        <nav className="flex-1 px-4 space-y-1 mt-4 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname.startsWith(item.path);
            return (
              <Link
                key={item.label}
                to={item.path}
                className={clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors font-medium text-sm',
                  isActive
                    ? 'bg-primary/10 text-primary font-semibold'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'
                )}
              >
                <Icon className="size-5" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-3 px-2 py-3 bg-slate-50 dark:bg-slate-800 rounded-xl">
            <div
              className="size-10 rounded-full bg-cover bg-center bg-slate-300 dark:bg-slate-700 flex items-center justify-center text-slate-600 dark:text-slate-400"
              style={userInfo?.avatar_url ? { backgroundImage: `url('${userInfo.avatar_url}')` } : undefined}
            >
              {!userInfo?.avatar_url && (
                <span className="text-sm font-bold">
                  {userInfo?.username?.charAt(0).toUpperCase() || 'U'}
                </span>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-bold truncate">{userInfo?.username || '用户'}</p>
              <p className="text-xs text-slate-500">SocialClaw 用户</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden relative">
        <Outlet />
      </main>
    </div>
  );
}
