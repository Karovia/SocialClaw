"""
Agent API 路由
提供：
- GET /api/v1/agents - 获取用户 Agent 列表
- GET /api/v1/agents/{agent_id} - 获取 Agent 详情
- PUT /api/v1/agents/{agent_id} - 更新 Agent 配置
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.auth import get_current_user
from app.models.user import User
from app.models.connected_agent import ConnectedAgent
from app.database import get_db
from app.services.agent_service import (
    get_user_agents,
    get_agent_by_id,
    update_agent_profile,
    create_agent
)
from app.schemas.agent import (
    AgentProfileUpdateRequest,
    AgentProfileResponse
)

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("/me")
async def list_my_agents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的 Agent 列表（兼容前端）

    需要认证：在 Header 中携带 JWT Token
    Authorization: Bearer {access_token}

    Returns:
        agents: Agent 列表（直接返回数组）
    """
    agents = await get_user_agents(db, current_user.user_id)

    return {
        "code": 0,
        "data": [
            {
                "agent_id": agent.agent_id,
                "user_id": agent.user_id,
                "name": agent.name,
                "description": agent.description,
                "interests": agent.get_interests(),
                "autonomy_level": agent.autonomy_level,
                "is_active": agent.is_active,
                "last_active_at": agent.last_active_at.isoformat() if agent.last_active_at else None,
                "connected_at": agent.connected_at.isoformat() if agent.connected_at else None,
                "updated_at": agent.updated_at.isoformat() if agent.updated_at else None
            }
            for agent in agents
        ]
    }


@router.get("/")
async def list_user_agents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的 Agent 列表

    需要认证：在 Header 中携带 JWT Token
    Authorization: Bearer {access_token}

    Returns:
        agents: Agent 列表
    """
    agents = await get_user_agents(db, current_user.user_id)

    return {
        "code": 0,
        "data": {
            "agents": [
                {
                    "agent_id": agent.agent_id,
                    "user_id": agent.user_id,
                    "name": agent.name,
                    "description": agent.description,
                    "interests": agent.get_interests(),
                    "autonomy_level": agent.autonomy_level,
                    "is_active": agent.is_active,
                    "last_active_at": agent.last_active_at.isoformat() if agent.last_active_at else None,
                    "connected_at": agent.connected_at.isoformat() if agent.connected_at else None,
                    "updated_at": agent.updated_at.isoformat() if agent.updated_at else None
                }
                for agent in agents
            ]
        }
    }


@router.get("/{agent_id}")
async def get_agent_detail(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取 Agent 详情

    需要认证：在 Header 中携带 JWT Token
    Authorization: Bearer {access_token}

    Args:
        agent_id: Agent ID

    Returns:
        agent: Agent 详情
    """
    agent = await get_agent_by_id(db, agent_id, current_user.user_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    return {
        "code": 0,
        "data": {
            "agent": {
                "agent_id": agent.agent_id,
                "user_id": agent.user_id,
                "name": agent.name,
                "description": agent.description,
                "interests": agent.get_interests(),
                "autonomy_level": agent.autonomy_level,
                "is_active": agent.is_active,
                "last_active_at": agent.last_active_at.isoformat() if agent.last_active_at else None,
                "connected_at": agent.connected_at.isoformat() if agent.connected_at else None,
                "updated_at": agent.updated_at.isoformat() if agent.updated_at else None
            }
        }
    }


@router.put("/{agent_id}")
async def update_agent(
    agent_id: str,
    request: AgentProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新 Agent 配置

    需要认证：在 Header 中携带 JWT Token
    Authorization: Bearer {access_token}

    Args:
        agent_id: Agent ID
        request: AgentProfileUpdateRequest

    Returns:
        agent: 更新后的 Agent 详情
    """
    try:
        agent = await update_agent_profile(
            db=db,
            agent_id=agent_id,
            user_id=current_user.user_id,
            update_data=request
        )

        return {
            "code": 0,
            "data": {
                "agent": {
                    "agent_id": agent.agent_id,
                    "user_id": agent.user_id,
                    "name": agent.name,
                    "description": agent.description,
                    "interests": agent.get_interests(),
                    "autonomy_level": agent.autonomy_level,
                    "is_active": agent.is_active,
                    "last_active_at": agent.last_active_at.isoformat() if agent.last_active_at else None,
                    "connected_at": agent.connected_at.isoformat() if agent.connected_at else None,
                    "updated_at": agent.updated_at.isoformat() if agent.updated_at else None
                }
            },
            "message": "Agent 配置更新成功"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.post("/")
async def create_new_agent(
    request: AgentProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建新的 Agent

    需要认证：在 Header 中携带 JWT Token
    Authorization: Bearer {access_token}

    Args:
        request: AgentProfileUpdateRequest

    Returns:
        agent: 新创建的 Agent 详情
    """
    try:
        agent = await create_agent(
            db=db,
            user_id=current_user.user_id,
            name=request.name,
            description=request.description,
            interests=request.interests,
            autonomy_level=request.autonomy_level
        )

        return {
            "code": 0,
            "data": {
                "agent": {
                    "agent_id": agent.agent_id,
                    "user_id": agent.user_id,
                    "name": agent.name,
                    "description": agent.description,
                    "interests": agent.get_interests(),
                    "autonomy_level": agent.autonomy_level,
                    "is_active": agent.is_active,
                    "last_active_at": agent.last_active_at.isoformat() if agent.last_active_at else None,
                    "connected_at": agent.connected_at.isoformat() if agent.connected_at else None,
                    "updated_at": agent.updated_at.isoformat() if agent.updated_at else None
                }
            },
            "message": "Agent 创建成功"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")
