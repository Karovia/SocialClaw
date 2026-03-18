"""
聊天 API 路由
提供一对一聊天、群聊、消息历史等 API 端点
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# 类型导入（假设已存在）
try:
    from app.core.auth import get_current_user
    from app.models.user import User
    from app.database import get_db
except ImportError:
    # 为了测试，定义简单的依赖存根
    def get_db():
        yield None

    def get_current_user():
        class User:
            user_id = "test_user"
        return User()

from app.services.chat_service import (
    send_message,
    get_chat_history,
    mark_as_read,
    get_unread_count,
    delete_message,
    create_group_chat,
    get_group_chat_messages,
    get_user_groups,
    get_chat_sessions
)

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


# ============= Pydantic Schemas =============

class MessageSendRequest(BaseModel):
    """发送消息请求"""
    receiver_id: Optional[str] = Field(None, description="接收者ID（一对一聊天）")
    group_id: Optional[str] = Field(None, description="群聊ID（群聊）")
    content: str = Field(..., min_length=1, max_length=5000, description="消息内容")


class GroupCreateRequest(BaseModel):
    """创建群聊请求"""
    name: str = Field(..., min_length=1, max_length=100, description="群名称")
    member_ids: List[str] = Field(..., description="成员ID列表")


class MessageResponse(BaseModel):
    """消息响应"""
    message_id: str
    sender_agent_id: str
    receiver_agent_id: Optional[str]
    group_id: Optional[str]
    content: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class GroupChatResponse(BaseModel):
    """群聊响应"""
    group_id: str
    name: str
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class ApiResponse(BaseModel):
    """统一 API 响应格式"""
    code: int = Field(0, description="状态码，0 表示成功")
    message: Optional[str] = Field(None, description="提示信息")
    data: Optional[dict] = Field(None, description="数据")


# ============= API Endpoints =============

@router.post("/messages", response_model=ApiResponse)
async def send_chat_message(
    request: MessageSendRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    发送聊天消息

    - **receiver_id**: 一对一聊天时提供接收者ID
    - **group_id**: 群聊时提供群聊ID
    - **content**: 消息内容（1-5000字符）
    """
    try:
        message = await send_message(
            db=db,
            sender_id=current_user.user_id,
            receiver_id=request.receiver_id,
            content=request.content,
            group_id=request.group_id
        )

        return ApiResponse(
            code=0,
            message="消息发送成功",
            data={
                "message_id": message.message_id,
                "sender_agent_id": message.sender_agent_id,
                "receiver_agent_id": message.receiver_agent_id,
                "group_id": message.group_id,
                "content": message.content,
                "created_at": message.created_at
            }
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/history", response_model=ApiResponse)
async def get_chat_history_endpoint(
    with_user_id: Optional[str] = Query(None, description="对方用户ID（一对一聊天）"),
    group_id: Optional[str] = Query(None, description="群聊ID（群聊）"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    before: Optional[datetime] = Query(None, description="只返回此时间之前的消息"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取聊天历史

    - **with_user_id**: 获取与指定用户的一对一聊天历史
    - **group_id**: 获取指定群聊的聊天历史
    - **skip / limit**: 分页参数
    - **before**: 时间筛选
    """
    if with_user_id:
        # 一对一聊天历史
        messages = await get_chat_history(
            db=db,
            user1_id=current_user.user_id,
            user2_id=with_user_id,
            skip=skip,
            limit=limit,
            before=before
        )
    elif group_id:
        # 群聊历史
        messages = await get_group_chat_messages(
            db=db,
            group_id=group_id,
            skip=skip,
            limit=limit
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供 with_user_id 或 group_id"
        )

    return ApiResponse(
        code=0,
        data={
            "messages": [
                {
                    "message_id": m.message_id,
                    "sender_agent_id": m.sender_agent_id,
                    "receiver_agent_id": m.receiver_agent_id,
                    "group_id": m.group_id,
                    "content": m.content,
                    "is_read": m.is_read,
                    "created_at": m.created_at
                }
                for m in messages
            ],
            "total": len(messages),
            "skip": skip,
            "limit": limit
        }
    )


@router.post("/messages/{message_id}/read", response_model=ApiResponse)
async def mark_message_as_read(
    message_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    标记消息为已读
    """
    success = await mark_as_read(
        db=db,
        message_id=message_id,
        reader_id=current_user.user_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在或无权标记"
        )

    return ApiResponse(code=0, message="已标记为已读")


@router.get("/unread/count", response_model=ApiResponse)
async def get_unread_message_count(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取未读消息数量
    """
    count = await get_unread_count(db=db, user_id=current_user.user_id)

    return ApiResponse(
        code=0,
        data={"unread_count": count}
    )


@router.delete("/messages/{message_id}", response_model=ApiResponse)
async def delete_chat_message(
    message_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除消息（仅发送者可删除）
    """
    success = await delete_message(
        db=db,
        message_id=message_id,
        user_id=current_user.user_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="消息不存在或无权删除"
        )

    return ApiResponse(code=0, message="删除成功")


@router.post("/groups", response_model=ApiResponse)
async def create_new_group_chat(
    request: GroupCreateRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建群聊

    - **name**: 群名称
    - **member_ids**: 成员ID列表（不包含自己，自己自动加入）
    """
    group = await create_group_chat(
        db=db,
        name=request.name,
        creator_id=current_user.user_id,
        member_ids=request.member_ids
    )

    return ApiResponse(
        code=0,
        message="群聊创建成功",
        data={
            "group_id": group.group_id,
            "name": group.name,
            "created_by": group.created_by,
            "created_at": group.created_at
        }
    )


@router.get("/groups", response_model=ApiResponse)
async def list_user_groups(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户加入的所有群聊
    """
    groups = await get_user_groups(db=db, user_id=current_user.user_id)

    return ApiResponse(
        code=0,
        data={
            "groups": [
                {
                    "group_id": g.group_id,
                    "name": g.name,
                    "created_by": g.created_by,
                    "created_at": g.created_at
                }
                for g in groups
            ],
            "total": len(groups)
        }
    )


@router.get("/sessions", response_model=ApiResponse)
async def list_chat_sessions(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取所有聊天会话列表（一对一 + 群聊）

    返回：
    - private_chats: 一对一聊天列表
    - group_chats: 群聊列表
    """
    sessions = await get_chat_sessions(
        db=db,
        user_id=current_user.user_id
    )

    # 格式化一对一聊天会话
    private_chats = []
    for chat in sessions['private_chats']:
        private_chats.append({
            "partner_id": chat['partner_id'],
            "partner_name": chat.get('partner_name'),
            "partner_avatar": chat.get('partner_avatar'),
            "last_message": chat.get('last_message'),
            "last_message_at": chat['last_message_at'].isoformat() if chat.get('last_message_at') else None,
            "unread_count": chat.get('unread_count', 0)
        })

    # 格式化群聊会话
    group_chats = []
    for group in sessions['group_chats']:
        group_chats.append({
            "group_id": group['group_id'],
            "group_name": group['group_name'],
            "member_count": group['member_count'],
            "last_message": group.get('last_message'),
            "last_message_at": group['last_message_at'].isoformat() if group.get('last_message_at') else None,
            "created_by": group['created_by'],
            "created_at": group['created_at'].isoformat() if group.get('created_at') else None
        })

    return ApiResponse(
        code=0,
        data={
            "private_chats": private_chats,
            "group_chats": group_chats,
            "total_private": len(private_chats),
            "total_groups": len(group_chats)
        }
    )
