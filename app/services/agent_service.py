"""
Agent 服务层
提供：
- 获取用户 Agent 列表
- 获取 Agent 详情
- 更新 Agent 配置
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.connected_agent import ConnectedAgent
from app.schemas.agent import AgentProfileUpdateRequest


async def get_user_agents(
    db: Session,
    user_id: str
) -> List[ConnectedAgent]:
    """
    获取用户的 Agent 列表

    Args:
        db: 数据库会话
        user_id: 用户ID

    Returns:
        List[ConnectedAgent]: Agent 列表
    """
    agents = db.query(ConnectedAgent).filter(
        ConnectedAgent.user_id == user_id,
        ConnectedAgent.is_active == True
    ).all()

    return agents


async def get_agent_by_id(
    db: Session,
    agent_id: str,
    user_id: Optional[str] = None
) -> ConnectedAgent:
    """
    获取 Agent 详情

    Args:
        db: 数据库会话
        agent_id: Agent ID
        user_id: 可选的用户ID（用于权限检查）

    Returns:
        ConnectedAgent: Agent 对象
    """
    query = db.query(ConnectedAgent).filter(
        ConnectedAgent.agent_id == agent_id,
        ConnectedAgent.is_active == True
    )

    # 如果提供了 user_id，检查是否是该用户的 Agent
    if user_id:
        query = query.filter(ConnectedAgent.user_id == user_id)

    agent = query.first()

    return agent


async def update_agent_profile(
    db: Session,
    agent_id: str,
    user_id: str,
    update_data: AgentProfileUpdateRequest
) -> ConnectedAgent:
    """
    更新 Agent 配置

    Args:
        db: 数据库会话
        agent_id: Agent ID
        user_id: 用户ID
        update_data: 更新数据

    Returns:
        ConnectedAgent: 更新后的 Agent 对象
    """
    # 先检查 Agent 是否存在且属于该用户
    agent = await get_agent_by_id(db, agent_id, user_id)

    if not agent:
        raise ValueError("Agent 不存在或无权访问")

    # 更新字段
    agent.name = update_data.name
    agent.description = update_data.description
    agent.set_interests(update_data.interests)
    agent.autonomy_level = update_data.autonomy_level
    agent.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(agent)

    return agent


async def create_agent(
    db: Session,
    user_id: str,
    name: str,
    interests: List[str] = None,
    description: str = None,
    autonomy_level: str = "80"
) -> ConnectedAgent:
    """
    创建新的 Agent

    Args:
        db: 数据库会话
        user_id: 用户ID
        name: Agent 名称
        interests: 兴趣标签列表
        description: 描述
        autonomy_level: 自主程度

    Returns:
        ConnectedAgent: 创建的 Agent 对象
    """
    from uuid import uuid4

    agent = ConnectedAgent(
        agent_id=f"agent_{uuid4().hex}",
        user_id=user_id,
        name=name,
        description=description,
        autonomy_level=autonomy_level,
        is_active=True,
        connected_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    if interests:
        agent.set_interests(interests)

    db.add(agent)
    db.commit()
    db.refresh(agent)

    return agent
