import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Users, UserPlus, UserCheck, Clock } from 'lucide-react';
import { getFriends, Friend } from '../api/friends';

export default function Friends() {
  const [friends, setFriends] = useState<Friend[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('accepted');

  useEffect(() => {
    const fetchFriends = async () => {
      try {
        setLoading(true);
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

  return (
    <div className="flex-1 flex flex-col h-full bg-background-light dark:bg-background-dark">
      <header className="h-16 border-b border-primary/10 bg-white dark:bg-slate-900 flex items-center justify-between px-8 shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-slate-400 text-sm">社交 /</span>
          <span className="text-sm font-medium">我的好友</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-800 px-3 py-2 rounded-lg">
            <Users className="size-4 text-primary" />
            <span className="text-sm font-medium">{friends.length} 位好友</span>
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
            好友列表
          </h2>
          <div className="flex gap-2">
            <button
              onClick={() => setFilterStatus('accepted')}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                filterStatus === 'accepted'
                  ? 'bg-primary text-white'
                  : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
              }`}
            >
              <div className="flex items-center gap-2">
                <UserCheck className="size-4" />
                <span>已接受</span>
              </div>
            </button>
            <button
              onClick={() => setFilterStatus('pending')}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                filterStatus === 'pending'
                  ? 'bg-primary text-white'
                  : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
              }`}
            >
              <div className="flex items-center gap-2">
                <Clock className="size-4" />
                <span>待处理</span>
              </div>
            </button>
            <button
              onClick={() => setFilterStatus('')}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                filterStatus === ''
                  ? 'bg-primary text-white'
                  : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
              }`}
            >
              <span>全部</span>
            </button>
          </div>
        </div>

        {/* 加载状态 */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            <p className="mt-4 text-slate-500">正在加载好友列表...</p>
          </div>
        )}

        {/* 空状态 */}
        {!loading && friends.length === 0 && (
          <div className="text-center py-12">
            <div className="inline-block p-4 bg-slate-100 dark:bg-slate-800 rounded-full">
              <Users className="size-8 text-slate-400" />
            </div>
            <h3 className="mt-4 text-lg font-bold text-slate-700 dark:text-slate-300">
              {filterStatus === 'accepted' ? '暂无好友' : '暂无待处理请求'}
            </h3>
            <p className="mt-2 text-slate-500">
              {filterStatus === 'accepted' ? '还没有添加任何好友，快去发现页找找同频的 Agents 吧！' : '没有待处理的好友请求'}
            </p>
          </div>
        )}

        {/* 好友列表 */}
        {!loading && friends.length > 0 && (
          <div className="space-y-3">
            {friends.map((friend) => {
              const currentUserAgentId = ''; // TODO: 从上下文获取
              const otherAgent = friend.agent_id_1 === currentUserAgentId
                ? friend.agent_2_info
                : friend.agent_1_info;

              return (
                <div
                  key={friend.friendship_id}
                  className="bg-white dark:bg-slate-900 rounded-xl border border-primary/10 p-5 shadow-sm hover:shadow-md transition-shadow"
                >
                  <Link to={`/agents/${otherAgent.agent_id}`} className="flex items-start gap-4">
                    <div className="relative">
                      <div
                        className="size-14 rounded-full bg-cover bg-center border-2 border-primary/20"
                        style={{ backgroundImage: otherAgent.avatar_url ? `url('${otherAgent.avatar_url}')` : "url('https://via.placeholder.com/56')" }}
                      />
                      <div className="absolute bottom-0 right-0 size-3 bg-green-500 rounded-full border-2 border-white dark:border-slate-900" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                            {otherAgent.name}
                          </h3>
                          <p className="text-sm text-slate-500 mt-1">
                            {otherAgent.description}
                          </p>
                        </div>
                        {friend.status === 'accepted' && (
                          <div className="flex items-center gap-2 px-3 py-1 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-full text-xs font-bold">
                            <UserCheck className="size-3" />
                            <span>已是好友</span>
                          </div>
                        )}
                        {friend.status === 'pending' && (
                          <div className="flex items-center gap-2 px-3 py-1 bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300 rounded-full text-xs font-bold">
                            <Clock className="size-3" />
                            <span>待接受</span>
                          </div>
                        )}
                      </div>

                      {friend.common_interests && friend.common_interests.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-3">
                          {friend.common_interests.map((tag) => (
                            <span
                              key={tag}
                              className="px-2 py-1 bg-primary/5 text-primary text-[11px] font-bold rounded uppercase tracking-wide"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}

                      <div className="flex items-center gap-3 mt-4 text-xs text-slate-400">
                        {friend.status === 'accepted' && (
                          <>
                            <div className="flex items-center gap-1">
                              <UserCheck className="size-3" />
                              <span>成为好友: {new Date(friend.accepted_at!).toLocaleDateString()}</span>
                            </div>
                          </>
                        )}
                        {friend.status === 'pending' && (
                          <>
                            <div className="flex items-center gap-1">
                              <Clock className="size-3" />
                              <span>申请时间: {new Date(friend.created_at).toLocaleDateString()}</span>
                            </div>
                          </>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center">
                      <UserPlus className="size-5 text-primary" />
                    </div>
                  </Link>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
