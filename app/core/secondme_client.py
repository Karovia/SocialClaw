"""
Second Me API 客户端封装

提供与 Second Me API 交互的所有功能，包括：
- 获取软记忆
- 获取兴趣标签（shades）
- 生成帖子内容
- 上报 Agent 行为到记忆系统
"""

import httpx
from typing import Dict, List, Optional
from datetime import datetime
import json
import hashlib
from functools import lru_cache

from app.core.config import settings
from app.core.logger import logger


class SecondMeClient:
    """Second Me API 客户端"""

    def __init__(self, access_token: str):
        """
        初始化 Second Me 客户端

        Args:
            access_token: Second Me API 访问令牌
        """
        self.access_token = access_token
        self.base_url = settings.SECOND_ME_API_BASE_URL.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=30.0
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def get_soft_memory(self, limit: int = 20) -> List[Dict]:
        """
        获取用户的软记忆列表

        Args:
            limit: 返回的记忆条数限制，默认 20

        Returns:
            软记忆列表，每个记忆包含 id, content, timestamp, type, importance 等字段
            失败时返回空列表
        """
        try:
            params = {"limit": limit} if limit else {}
            response = await self.client.get("/api/secondme/user/softmemory", params=params)
            response.raise_for_status()

            data = response.json()
            if data.get("code") == 0 and "data" in data and "list" in data["data"]:
                return data["data"]["list"]
            else:
                logger.warning(f"Second Me API returned unexpected response: {data}")
                return []

        except Exception as e:
            logger.error(f"Failed to get soft memory: {e}")
            return []

    async def get_shades(self) -> List[str]:
        """
        获取用户的兴趣标签（shades）

        Returns:
            兴趣标签字符串列表
            失败时返回空列表
        """
        try:
            response = await self.client.get("/api/secondme/user/shades")
            response.raise_for_status()

            data = response.json()
            if data.get("code") == 0 and "data" in data and "shades" in data["data"]:
                return data["data"]["shades"]
            else:
                logger.warning(f"Second Me API returned unexpected response for shades: {data}")
                return []

        except Exception as e:
            logger.error(f"Failed to get shades: {e}")
            return []

    async def generate_post_content(
        self,
        memory_content: str,
        interest_tags: List[str],
        max_tokens: int = 300
    ) -> Optional[str]:
        """
        使用 Second Me Chat API 生成帖子内容

        Args:
            memory_content: 软记忆内容片段
            interest_tags: 兴趣标签列表
            max_tokens: 最大生成 token 数，默认 300

        Returns:
            生成的帖子内容字符串，失败时返回 None
        """
        try:
            # 构造系统提示词和用户消息
            system_prompt = (
                "你是一个活跃的社交网络用户，基于你的个人经历和兴趣来创作自然、真实的社交媒体帖子。"
                "请根据提供的记忆片段和兴趣标签，创作一个简短、有吸引力的帖子内容。"
            )

            user_message = (
                f"基于以下记忆：'{memory_content}' "
                f"和我的兴趣：{', '.join(interest_tags)}，"
                f"请创作一个不超过{max_tokens}个token的社交媒体帖子。"
            )

            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": max_tokens,
                "stream": False
            }

            response = await self.client.post("/api/secondme/chat/stream", json=payload)
            response.raise_for_status()

            data = response.json()
            if data.get("code") == 0 and "data" in data:
                # 假设响应中包含生成的内容
                generated_content = data["data"].get("content") or data["data"].get("message")
                if generated_content:
                    return str(generated_content)

            logger.warning(f"Second Me Chat API returned unexpected response: {data}")
            return None

        except Exception as e:
            logger.error(f"Failed to generate post content: {e}")
            return None

    async def ingest_agent_memory(
        self,
        action: str,
        refs: List[Dict],
        channel_kind: str = "socialclaw",
        **kwargs
    ) -> Dict:
        """
        上报 Agent 行为到 Second Me 记忆系统

        Args:
            action: 动作类型（如 "post_created", "friend_request_sent"）
            refs: 证据指针数组，每个元素包含 eventId, objectType, objectId
            channel_kind: 频道类型，默认 "socialclaw"
            **kwargs: 其他可选参数

        Returns:
            响应数据 {eventId, isDuplicate}，失败时返回空字典
        """
        try:
            payload = {
                "action": action,
                "refs": refs,
                "channelKind": channel_kind,
                **kwargs
            }

            response = await self.client.post("/api/secondme/agent_memory/ingest", json=payload)
            response.raise_for_status()

            data = response.json()
            if data.get("code") == 0 and "data" in data:
                return data["data"]
            else:
                logger.warning(f"Second Me ingest API returned unexpected response: {data}")
                return {}

        except Exception as e:
            logger.error(f"Failed to ingest agent memory: {e}")
            return {}

    @staticmethod
    def generate_idempotency_key(object_type: str, object_id: str) -> str:
        """
        生成幂等键，防止重复上报

        Args:
            object_type: 对象类型
            object_id: 对象ID

        Returns:
            SHA256 哈希字符串作为幂等键
        """
        key_string = f"external:{object_type}:{object_id}"
        return hashlib.sha256(key_string.encode('utf-8')).hexdigest()


# 全局客户端缓存
@lru_cache(maxsize=128)
def get_secondme_client(access_token: str) -> SecondMeClient:
    """
    获取 Second Me 客户端实例（带缓存）

    Args:
        access_token: Second Me API 访问令牌

    Returns:
        SecondMeClient 实例
    """
    return SecondMeClient(access_token)