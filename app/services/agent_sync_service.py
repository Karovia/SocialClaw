"""
Agent 同步服务

从 Second Me 同步用户信息到 SocialClaw
"""
import json
from typing import List, Dict, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from app.models.connected_agent import ConnectedAgent
from app.core.secondme_client import SecondMeClient
from app.core.logger import logger


async def sync_connected_agents(
    db: Session,
    user_id: str,
    second_me_token: str
) -> bool:
    """
    从 Second Me 同步用户的所有 ConnectedAgent

    流程：
    1. 获取 Second Me 用户信息
    2. 获取兴趣标签
    3. 创建/更新 ConnectedAgent 记录

    Args:
        db: 数据库会话
        user_id: SocialClaw 用户 ID
        second_me_token: Second Me Access Token

    Returns:
        bool: 同步是否成功
    """
    try:
        async with SecondMeClient(second_me_token) as client:
            # 1. 获取用户信息
            logger.info(f"获取 Second Me 用户信息: {user_id}")
            user_info = await client.get_user_info()

            if not user_info or not user_info.get("userId"):
                logger.error(f"获取用户信息失败: {user_info}")
                return False

            # 2. 获取兴趣标签
            logger.info(f"获取 Second Me 兴趣标签: {user_id}")
            shades = await client.get_shades()

            # 3. 创建 ConnectedAgent
            #    （一个用户对应一个 Agent，使用 Second Me 信息填充）
            agent_id = f"agent_{user_id}"
            agent = db.query(ConnectedAgent).filter(
                ConnectedAgent.agent_id == agent_id
            ).first()

            if not agent:
                # 首次创建
                logger.info(f"创建 ConnectedAgent: {agent_id}")
                agent = ConnectedAgent(
                    agent_id=agent_id,
                    user_id=user_id,
                    name=user_info.get("name", "我的 Agent"),
                    description="基于 Second Me 软记忆的自主社交 Agent",
                    interests=json.dumps(shades or ["生活", "日常"]),
                    autonomy_level="80",
                    auto_post_enabled=True,
                    post_interval_hours=12,
                    auto_friend_enabled=True,
                    friend_request_limit_per_day=3,
                    max_friends=100,
                    is_active=True
                )
                db.add(agent)
                db.commit()
                db.refresh(agent)
                logger.info(f"✓ ConnectedAgent {agent_id} 创建成功")
            else:
                # 更新信息
                logger.info(f"更新 ConnectedAgent: {agent_id}")
                agent.name = user_info.get("name", agent.name)
                agent.interests = json.dumps(shades or agent.get_interests())
                agent.is_active = True
                agent.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(agent)
                logger.info(f"✓ ConnectedAgent {agent_id} 更新成功")

        return True

    except Exception as e:
        logger.error(f"✗ ConnectedAgent 同步失败: {e}", exc_info=True)
        db.rollback()
        return False


async def get_second_me_user_info(
    second_me_token: str
) -> Optional[Dict]:
    """
    获取 Second Me 用户信息（独立函数，用于其他场景）

    Args:
        second_me_token: Second Me Access Token

    Returns:
        Dict: 用户信息字典
    """
    try:
        async with SecondMeClient(second_me_token) as client:
            user_info = await client.get_user_info()
            return user_info
    except Exception as e:
        logger.error(f"获取 Second Me 用户信息失败: {e}")
        return None


async def get_second_me_shades(
    second_me_token: str
) -> List[str]:
    """
    获取 Second Me 兴趣标签（独立函数，用于其他场景）

    Args:
        second_me_token: Second Me Access Token

    Returns:
        List[str]: 兴趣标签列表
    """
    try:
        async with SecondMeClient(second_me_token) as client:
            shades = await client.get_shades()
            return shades or []
    except Exception as e:
        logger.error(f"获取 Second Me 兴趣标签失败: {e}")
        return []
