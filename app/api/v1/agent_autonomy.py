from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.auth import get_current_user
from app.models.user import User
from app.database import get_db
from app.services.agent_autonomy_service import (
    agent_auto_post,
    update_agent_autonomy_config
)
from app.services.agent_service import get_agent_by_id
from app.models.agent_autonomy_log import AgentAutonomyLog
from app.schemas.agent_autonomy import (
    GeneratePostRequest,
    GeneratePostResponse,
    AgentAutonomyConfig,
    AgentActionLog
)


router = APIRouter(prefix="/agent-autonomy", tags=["Agent Autonomy"])


@router.post("/{agent_id}/generate-post")
async def generate_post(
    agent_id: str,
    request: Optional[GeneratePostRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    手动生成帖子

    触发 Agent 立即生成一条帖子（不等待定时任务）

    Args:
        agent_id: Agent ID
        request: 生成请求参数（可选）

    Returns:
        GeneratePostResponse: 生成的帖子信息
    """
    # 检查 Agent 是否属于当前用户
    agent = await get_agent_by_id(db, agent_id, current_user.user_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found or access denied")

    # 执行自动发帖
    success = await agent_auto_post(agent_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to generate post")

    # 获取最新创建的帖子
    from app.services.post_service import get_post_list
    posts = get_post_list(db, skip=0, limit=1)
    if not posts:
        raise HTTPException(status_code=500, detail="Post created but not found in database")

    latest_post = posts[0]

    # 返回帖子信息
    return GeneratePostResponse(
        post_id=latest_post.post_id,
        content=latest_post.content,
        topic=latest_post.topic,
        created_at=latest_post.created_at
    )


@router.put("/{agent_id}/config")
async def update_autonomy_config(
    agent_id: str,
    config: AgentAutonomyConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新 Agent 自主行为配置

    Args:
        agent_id: Agent ID
        config: 自主行为配置

    Returns:
        配置更新结果
    """
    # 检查 Agent 是否属于当前用户
    agent = await get_agent_by_id(db, agent_id, current_user.user_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found or access denied")

    # 转换为字典
    config_dict = config.dict()

    # 更新配置
    success = update_agent_autonomy_config(db, agent_id, config_dict)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update autonomy configuration")

    return {"message": "Configuration updated successfully"}


@router.get("/{agent_id}/logs")
async def get_agent_logs(
    agent_id: str,
    action_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取 Agent 行为日志

    Args:
        agent_id: Agent ID
        action_type: 筛选行为类型（可选）
        limit: 返回数量上限
        offset: 跳过数量

    Returns:
        Agent 行为日志列表
    """
    # 检查 Agent 是否属于当前用户
    agent = await get_agent_by_id(db, agent_id, current_user.user_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found or access denied")

    # 查询日志
    query = db.query(AgentAutonomyLog).filter(
        AgentAutonomyLog.agent_id == agent_id,
        AgentAutonomyLog.user_id == current_user.user_id
    )

    if action_type:
        query = query.filter(AgentAutonomyLog.action_type == action_type)

    total_count = query.count()
    logs = query.order_by(AgentAutonomyLog.created_at.desc()).offset(offset).limit(limit).all()

    # 转换为响应格式
    log_responses = []
    for log in logs:
        log_dict = log.to_dict()
        log_responses.append(AgentActionLog(**log_dict))

    # 返回日志列表和总数
    return {
        "logs": log_responses,
        "total": total_count,
        "limit": limit,
        "offset": offset
    }


@router.get("/{agent_id}/stats")
async def get_agent_stats(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取 Agent 行为统计

    Args:
        agent_id: Agent ID

    Returns:
        Agent 行为统计数据
    """
    # 检查 Agent 是否属于当前用户
    agent = await get_agent_by_id(db, agent_id, current_user.user_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found or access denied")

    # 统计总帖子数、总请求数
    from datetime import datetime, timedelta

    total_posts = db.query(AgentAutonomyLog).filter(
        AgentAutonomyLog.agent_id == agent_id,
        AgentAutonomyLog.action_type == "post_created",
        AgentAutonomyLog.success == True
    ).count()

    total_friend_requests = db.query(AgentAutonomyLog).filter(
        AgentAutonomyLog.agent_id == agent_id,
        AgentAutonomyLog.action_type == "friend_request_sent",
        AgentAutonomyLog.success == True
    ).count()

    # 统计今日数据
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    today_posts = db.query(AgentAutonomyLog).filter(
        AgentAutonomyLog.agent_id == agent_id,
        AgentAutonomyLog.action_type == "post_created",
        AgentAutonomyLog.success == True,
        AgentAutonomyLog.created_at >= today_start
    ).count()

    today_friend_requests = db.query(AgentAutonomyLog).filter(
        AgentAutonomyLog.agent_id == agent_id,
        AgentAutonomyLog.action_type == "friend_request_sent",
        AgentAutonomyLog.success == True,
        AgentAutonomyLog.created_at >= today_start
    ).count()

    # 返回统计数据
    return {
        "agent_id": agent_id,
        "total_posts": total_posts,
        "total_friend_requests": total_friend_requests,
        "today_posts": today_posts,
        "today_friend_requests": today_friend_requests,
        "autonomy_level": agent.autonomy_level,
        "auto_post_enabled": agent.auto_post_enabled,
        "auto_friend_enabled": agent.auto_friend_enabled
    }