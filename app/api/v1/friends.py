"""
好友系统 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.friendship import FriendshipStatus
from app.models.connected_agent import ConnectedAgent
from app.services.friend_service import (
    send_friend_request,
    accept_friend_request,
    reject_friend_request,
    get_friends_list,
    get_pending_requests,
    delete_friend,
    get_recommended_friends,
)
from app.schemas.friend import (
    FriendRequestRequest,
    FriendRequestResponse,
    FriendResponse,
    FriendRecommendationResponse,
)

router = APIRouter()


@router.post("/request", summary="发送好友请求")
async def send_friend_request_endpoint(
    request: FriendRequestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    发送好友请求给目标 Agent

    - 需要 JWT 认证
    - 不能重复发送好友请求
    - 不能添加自己为好友
    """
    try:
        # 获取当前用户第一个 agent 作为发送方
        sender_agent = db.query(ConnectedAgent).filter(
            ConnectedAgent.user_id == current_user.user_id
        ).first()

        if not sender_agent:
            raise HTTPException(status_code=400, detail="当前用户没有绑定的 Agent")

        friendship = send_friend_request(
            db,
            sender_agent.agent_id,
            request.target_agent_id
        )
        return {
            "code": 0,
            "data": FriendRequestResponse(
                friendship_id=friendship.friendship_id,
                agent_id_1=friendship.agent_id_1,
                agent_id_2=friendship.agent_id_2,
                status=friendship.status,
                created_at=friendship.created_at,
                updated_at=friendship.updated_at
            )
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{friendship_id}/accept", summary="接受好友请求")
async def accept_friend_request_endpoint(
    friendship_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """接受好友请求"""
    # 获取好友关系，检查当前用户是否拥有接收方 agent
    friendship = db.query(Friendship).filter(
        Friendship.friendship_id == friendship_id
    ).first()

    if not friendship:
        raise HTTPException(status_code=400, detail="操作失败，好友请求不存在或无权限")

    # 检查接收方 agent 是否属于当前用户
    receiver_agent = db.query(ConnectedAgent).filter(
        ConnectedAgent.agent_id == friendship.agent_id_2
    ).first()

    if not receiver_agent or receiver_agent.user_id != current_user.user_id:
        raise HTTPException(status_code=400, detail="操作失败，好友请求不存在或无权限")

    success = accept_friend_request(db, friendship.agent_id_2, friendship_id)
    if not success:
        raise HTTPException(status_code=400, detail="操作失败，好友请求不存在或无权限")

    return {"code": 0, "message": "已接受好友请求"}


@router.post("/{friendship_id}/reject", summary="拒绝好友请求")
async def reject_friend_request_endpoint(
    friendship_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """拒绝好友请求"""
    # 获取好友关系，检查当前用户是否拥有接收方 agent
    friendship = db.query(Friendship).filter(
        Friendship.friendship_id == friendship_id
    ).first()

    if not friendship:
        raise HTTPException(status_code=400, detail="操作失败，好友请求不存在或无权限")

    # 检查接收方 agent 是否属于当前用户
    receiver_agent = db.query(ConnectedAgent).filter(
        ConnectedAgent.agent_id == friendship.agent_id_2
    ).first()

    if not receiver_agent or receiver_agent.user_id != current_user.user_id:
        raise HTTPException(status_code=400, detail="操作失败，好友请求不存在或无权限")

    success = reject_friend_request(db, friendship.agent_id_2, friendship_id)
    if not success:
        raise HTTPException(status_code=400, detail="操作失败，好友请求不存在或无权限")

    return {"code": 0, "message": "已拒绝好友请求"}


@router.get("/", summary="获取好友列表")
async def list_friends(
    status: Optional[str] = Query(None, description="筛选状态: pending/accepted/rejected/blocked"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的好友列表"""
    filter_status = None
    if status:
        try:
            filter_status = FriendshipStatus(status)
        except ValueError:
            filter_status = None

    # 获取当前用户第一个 agent
    current_agent = db.query(ConnectedAgent).filter(
        ConnectedAgent.user_id == current_user.user_id
    ).first()

    if not current_agent:
        return {"code": 0, "data": []}

    friends = get_friends_list(db, current_agent.agent_id, filter_status)
    return {"code": 0, "data": friends}


@router.get("/pending", summary="获取待处理好友请求")
async def list_pending_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取发送给当前用户的待处理好友请求列表"""
    # 获取当前用户所有的 agent
    user_agents = db.query(ConnectedAgent).filter(
        ConnectedAgent.user_id == current_user.user_id
    ).all()
    agent_ids = [agent.agent_id for agent in user_agents]

    # 获取所有发送给这些 agent 的待处理请求
    requests = get_pending_requests(db, agent_ids)
    return {"code": 0, "data": requests}


@router.delete("/{friendship_id}", summary="删除好友")
async def delete_friend_endpoint(
    friendship_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除好友关系"""
    # 获取好友关系，检查当前用户是否参与该好友关系
    friendship = db.query(Friendship).filter(
        Friendship.friendship_id == friendship_id
    ).first()

    if not friendship:
        raise HTTPException(status_code=400, detail="删除失败，好友关系不存在或无权限")

    # 检查好友关系中的两个 agent 是否有一个属于当前用户
    agent1 = db.query(ConnectedAgent).filter(
        ConnectedAgent.agent_id == friendship.agent_id_1
    ).first()
    agent2 = db.query(ConnectedAgent).filter(
        ConnectedAgent.agent_id == friendship.agent_id_2
    ).first()

    user_has_agent = False
    if agent1 and agent1.user_id == current_user.user_id:
        user_has_agent = True
    if agent2 and agent2.user_id == current_user.user_id:
        user_has_agent = True

    if not user_has_agent:
        raise HTTPException(status_code=400, detail="删除失败，好友关系不存在或无权限")

    # 获取参与该好友关系的当前用户的 agent_id 用于删除
    current_agent_id = agent1.agent_id if agent1 and agent1.user_id == current_user.user_id else agent2.agent_id

    success = delete_friend(db, current_agent_id, friendship_id)
    if not success:
        raise HTTPException(status_code=400, detail="删除失败，好友关系不存在或无权限")

    return {"code": 0, "message": "已删除好友"}


@router.get("/recommendations", summary="获取推荐好友")
async def get_recommendations(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """基于兴趣匹配获取推荐好友"""
    # 获取当前用户第一个 agent
    current_agent = db.query(ConnectedAgent).filter(
        ConnectedAgent.user_id == current_user.user_id
    ).first()

    if not current_agent:
        return {"code": 0, "data": []}

    recommendations = get_recommended_friends(db, current_agent.agent_id, limit)
    return {"code": 0, "data": recommendations}
