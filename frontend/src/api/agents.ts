import api from './auth';
import { Agent } from '../types/agent';

/**
 * 获取当前用户的 Agent 列表
 */
export const getMyAgents = async (): Promise<Agent[]> => {
  const response = await api.get('/agents');

  if (response.data.code === 0) {
    return response.data.data.agents || [];
  }
  throw new Error(response.data.message || '获取 Agent 列表失败');
};

/**
 * 获取 Agent 详情
 */
export const getAgentDetail = async (agentId: string): Promise<Agent> => {
  const response = await api.get(`/agents/${agentId}`);

  if (response.data.code === 0) {
    return response.data.data.agent;
  }
  throw new Error(response.data.message || '获取 Agent 详情失败');
};

/**
 * 更新 Agent 配置
 */
export const updateAgentConfig = async (
  agentId: string,
  config: { autonomy_level?: number; interests?: string[]; description?: string }
): Promise<Agent> => {
  const response = await api.put(`/agents/${agentId}`, config);

  if (response.data.code !== 0) {
    throw new Error(response.data.message || '更新配置失败');
  }
  return response.data.data.agent;
};

/**
 * 创建新的 Agent
 */
export const createAgent = async (
  config: { name: string; description: string; interests: string[]; autonomy_level: number }
): Promise<Agent> => {
  const response = await api.post('/agents', config);

  if (response.data.code !== 0) {
    throw new Error(response.data.message || '创建 Agent 失败');
  }
  return response.data.data.agent;
};
