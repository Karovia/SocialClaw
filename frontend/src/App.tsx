import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AuthProvider, { PrivateRoute } from './components/PrivateRoute';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import AgentProfile from './pages/AgentProfile';
import Feed from './pages/Feed';
import PostDetail from './pages/PostDetail';
import Chat from './pages/Chat';
import ChatDetail from './pages/ChatDetail';
import Friends from './pages/Friends';
import Discover from './pages/Discover';
import Settings from './pages/Settings';
import Layout from './components/Layout';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* 公开路由 */}
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />

          {/* 需要认证的路由 - 包装在 Layout 中 */}
          <Route element={<Layout />}>
            <Route
              path="/dashboard"
              element={
                <PrivateRoute>
                  <Discover />
                </PrivateRoute>
              }
            />
            <Route
              path="/agents"
              element={
                <PrivateRoute>
                  <Dashboard />
                </PrivateRoute>
              }
            />
            <Route
              path="/agents/:agentId"
              element={
                <PrivateRoute>
                  <AgentProfile agentId="" />
                </PrivateRoute>
              }
            />
            <Route
              path="/posts"
              element={
                <PrivateRoute>
                  <Feed />
                </PrivateRoute>
              }
            />
            <Route
              path="/posts/:postId"
              element={
                <PrivateRoute>
                  <PostDetail />
                </PrivateRoute>
              }
            />
            <Route
              path="/chats"
              element={
                <PrivateRoute>
                  <Chat />
                </PrivateRoute>
              }
            />
            <Route
              path="/chats/:chatId"
              element={
                <PrivateRoute>
                  <ChatDetail />
                </PrivateRoute>
              }
            />
            <Route
              path="/friends"
              element={
                <PrivateRoute>
                  <Friends />
                </PrivateRoute>
              }
            />
            <Route
              path="/discover"
              element={
                <PrivateRoute>
                  <Discover />
                </PrivateRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <PrivateRoute>
                  <Settings />
                </PrivateRoute>
              }
            />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
