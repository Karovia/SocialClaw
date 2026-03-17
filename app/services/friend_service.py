"""
好友业务逻辑服务
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.friendship import Friendship, FriendshipStatus
from app.models.connected_agent import ConnectedAgent
from app.schemas.friend import FriendResponse, FriendRecommendationResponse
import uuid


def send_friend_request(db: Session, sender_id: str, receiver_id: str) -> Friendship:
    """
    发送好友请求

    Args:
        db: 数据库会话
        sender_id: 发送方 Agent ID
        receiver_id: 接收方 Agent ID

    Returns:
        创建的 Friendship 对象

    Raises:
        ValueError: 如果好友关系已存在或发送给自身
    """
    # 不能添加自己为好友
    if sender_id == receiver_id:
        raise ValueError("不能添加自己为好友")

    # 检查是否已经存在好友关系（任意方向）
    existing = db.query(Friendship).filter(
        or_(
            and_(Friendship.agent_id_1 == sender_id, Friendship.agent_id_2 == receiver_id),
            and_(Friendship.agent_id_1 == receiver_id, Friendship.agent_id_2 == sender_id)
        )
    ).first()

    if existing:
        raise ValueError("好友关系已存在")

    # 创建好友请求
    friendship = Friendship(
        friendship_id=f"friend_{uuid.uuid4().hex[:16]}",
        agent_id_1=sender_id,
        agent_id_2=receiver_id,
        status=FriendshipStatus.PENDING
    )

    db.add(friendship)
    db.commit()
    db.refresh(friendship)

    return friendship


def accept_friend_request(db: Session, user_id: str, friendship_id: str) -> bool:
    """
    接受好友请求

    Args:
        db: 数据库会话
        user_id: 当前用户 ID（必须是接收方）
        friendship_id: 好友关系 ID

    Returns:
        是否成功接受
    """
    friendship = db.query(Friendship).filter(
        Friendship.friendship_id == friendship_id
    ).first()

    if not friendship:
        return False

    # 必须是接收方才能接受
    if friendship.agent_id_2 != user_id:
        return False

    # 必须是待处理状态
    if friendship.status != FriendshipStatus.PENDING:
        return False

    friendship.status = FriendshipStatus.ACCEPTED
    friendship.updated_at = datetime.utcnow()
    db.commit()

    return True


def reject_friend_request(db: Session, user_id: str, friendship_id: str) -> bool:
    """
    拒绝好友请求

    Args:
        db: 数据库会话
        user_id: 当前用户 ID（必须是接收方）
        friendship_id: 好友关系 ID

    Returns:
        是否成功拒绝
    """
    friendship = db.query(Friendship).filter(
        Friendship.friendship_id == friendship_id
    ).first()

    if not friendship:
        return False

    if friendship.agent_id_2 != user_id:
        return False

    if friendship.status != FriendshipStatus.PENDING:
        return False

    friendship.status = FriendshipStatus.REJECTED
    friendship.updated_at = datetime.utcnow()
    db.commit()

    return True


def get_friends_list(
    db: Session,
    user_id: str,
    status: Optional[FriendshipStatus] = FriendshipStatus.ACCEPTED
) -> List[FriendResponse]:
    """
    获取用户的好友列表

    Args:
        db: 数据库会话
        user_id: 用户 Agent ID
        status: 筛选状态，默认为只返回已接受的好友

    Returns:
        好友信息列表
    """
    # 查询所有符合条件的好友关系
    friendships = db.query(Friendship).filter(
        or_(
            Friendship.agent_id_1 == user_id,
            Friendship.agent_id_2 == user_id
        ),
        Friendship.status == status
    ).all()

    result = []
    for friendship in friendships:
        # 判断对方是哪个 agent
        other_agent_id = (
            friendship.agent_id_2 if friendship.agent_id_1 == user_id
            else friendship.agent_id_1
        )

        # 获取对方 agent 信息
        agent = db.query(ConnectedAgent).filter(
            ConnectedAgent.agent_id == other_agent_id
        ).first()

        if agent:
            result.append(FriendResponse(
                agent_id=agent.agent_id,
                name=agent.name,
                description=agent.description,
                status=friendship.status,
                friendship_id=friendship.friendship_id,
                created_at=friendship.created_at
            ))

    return result


def get_pending_requests(db: Session, agent_ids: str | list[str]) -> List[Friendship]:
    """
    获取待处理的好友请求（发给当前用户的）

    Args:
        db: 数据库会话
        agent_ids: 用户的 Agent ID 或多个 Agent ID 列表

    Returns:
        待处理的好友请求列表
    """
    if isinstance(agent_ids, str):
        agent_ids = [agent_ids]

    return db.query(Friendship).filter(
        Friendship.agent_id_2.in_(agent_ids),
        Friendship.status == FriendshipStatus.PENDING
    ).order_by(Friendship.created_at.desc()).all()


def delete_friend(db: Session, user_id: str, friendship_id: str) -> bool:
    """
    删除好友关系

    Args:
        db: 数据库会话
        user_id: 当前用户 ID
        friendship_id: 好友关系 ID

    Returns:
        是否成功删除
    """
    friendship = db.query(Friendship).filter(
        Friendship.friendship_id == friendship_id
    ).first()

    if not friendship:
        return False

    # 检查用户是否在该好友关系中
    if friendship.agent_id_1 != user_id and friendship.agent_id_2 != user_id:
        return False

    db.delete(friendship)
    db.commit()

    return True


def get_recommended_friends(
    db: Session,
    user_id: str,
    limit: int = 10
) -> List[FriendRecommendationResponse]:
    """
    基于兴趣匹配获取推荐好友

    Args:
        db: 数据库会话
        user_id: 当前用户 ID
        limit: 返回数量限制

    Returns:
        推荐好友列表，按匹配度排序
    """
    # 获取当前用户信息
    current_agent = db.query(ConnectedAgent).filter(
        ConnectedAgent.agent_id == user_id
    ).first()

    if not current_agent:
        return []

    current_interests = set(current_agent.get_interests())

    # 获取已有的好友关系 ID（排除这些推荐）
    existing_friendships = db.query(Friendship).filter(
        or_(
            Friendship.agent_id_1 == user_id,
            Friendship.agent_id_2 == user_id
        )
    ).all()

    excluded_ids = {user_id}  # 排除自己
    for fs in existing_friendships:
        excluded_ids.add(fs.agent_id_1)
        excluded_ids.add(fs.agent_id_2)

    # 查询其他活跃 agent
    candidates = db.query(ConnectedAgent).filter(
        ConnectedAgent.is_active == True,
        ~ConnectedAgent.agent_id.in_(list(excluded_ids))
    ).all()

    # 计算匹配分数
    recommendations = []
    for candidate in candidates:
        candidate_interests = set(candidate.get_interests())

        # Jaccard 相似度
        if len(current_interests) == 0 or len(candidate_interests) == 0:
            match_score = 0.0
        else:
            intersection = len(current_interests & candidate_interests)
            union = len(current_interests | candidate_interests)
            match_score = intersection / union if union > 0 else 0.0

        recommendations.append(FriendRecommendationResponse(
            agent_id=candidate.agent_id,
            name=candidate.name,
            description=candidate.description,
            interests=candidate.get_interests(),
            match_score=match_score
        ))

    # 按匹配度降序排序，返回前 N 个
    recommendations.sort(key=lambda x: x.match_score, reverse=True)
    return recommendations[:limit]
