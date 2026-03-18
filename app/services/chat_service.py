"""
聊天服务模块
提供一对一聊天、群聊、消息历史记录等功能
"""
from typing import List, Optional
from datetime import datetime, UTC, timedelta
from sqlalchemy.orm import Session
import uuid

# 类型导入（假设已存在）
try:
    from app.models.chat_message import ChatMessage
    from app.models.group_chat import GroupChat
    from app.models.group_chat_member import GroupChatMember
    from app.models.user import User
    from app.models.connected_agent import ConnectedAgent
except ImportError:
    # 为了测试，定义简单的模型存根和 mock 列
    class MockColumn:
        """模拟 SQLAlchemy 列，支持 is_(), ==, 等操作"""
        def __init__(self, name):
            self.name = name

        def is_(self, other):
            return self

        def in_(self, other):
            return self

        def desc(self):
            return self

        def __eq__(self, other):
            return self

        def __ne__(self, other):
            return self

        def __lt__(self, other):
            return self

        def __le__(self, other):
            return self

        def __gt__(self, other):
            return self

        def __ge__(self, other):
            return self

        def __and__(self, other):
            return self

        def __or__(self, other):
            return self

    class ChatMessage:
        # 类级别属性，用于 SQLAlchemy 查询风格
        message_id = MockColumn("message_id")
        sender_agent_id = MockColumn("sender_agent_id")
        receiver_agent_id = MockColumn("receiver_agent_id")
        group_id = MockColumn("group_id")
        content = MockColumn("content")
        is_read = MockColumn("is_read")
        is_deleted = MockColumn("is_deleted")
        created_at = MockColumn("created_at")

        def __init__(self, **kwargs):
            self.message_id = kwargs.get('message_id')
            self.sender_agent_id = kwargs.get('sender_agent_id')
            self.receiver_agent_id = kwargs.get('receiver_agent_id')
            self.group_id = kwargs.get('group_id')
            self.content = kwargs.get('content')
            self.is_read = kwargs.get('is_read', False)
            self.is_deleted = kwargs.get('is_deleted', False)
            self.created_at = kwargs.get('created_at', datetime.now(UTC))

    class GroupChat:
        # 类级别属性
        group_id = MockColumn("group_id")
        name = MockColumn("name")
        created_by = MockColumn("created_by")
        is_deleted = MockColumn("is_deleted")
        created_at = MockColumn("created_at")

        def __init__(self, **kwargs):
            self.group_id = kwargs.get('group_id')
            self.name = kwargs.get('name')
            self.created_by = kwargs.get('created_by')
            self.is_deleted = kwargs.get('is_deleted', False)
            self.created_at = kwargs.get('created_at', datetime.now(UTC))

    class GroupChatMember:
        # 类级别属性
        group_id = MockColumn("group_id")
        agent_id = MockColumn("agent_id")
        joined_at = MockColumn("joined_at")

        def __init__(self, **kwargs):
            self.group_id = kwargs.get('group_id')
            self.agent_id = kwargs.get('agent_id')
            self.joined_at = kwargs.get('joined_at', datetime.now(UTC))


async def send_message(
    db: Session,
    sender_id: str,
    receiver_id: Optional[str] = None,
    content: str = "",
    group_id: Optional[str] = None
) -> ChatMessage:
    """
    发送消息（一对一或群聊）

    Args:
        db: 数据库会话
        sender_id: 发送者ID
        receiver_id: 接收者ID（一对一聊天时必需）
        content: 消息内容
        group_id: 群聊ID（群聊时必需）

    Returns:
        ChatMessage: 创建的消息对象

    Raises:
        ValueError: 参数错误时抛出
    """
    if not group_id and not receiver_id:
        raise ValueError("必须提供 receiver_id（一对一）或 group_id（群聊）")

    if not content or not content.strip():
        raise ValueError("消息内容不能为空")

    message = ChatMessage(
        message_id=f"msg_{uuid.uuid4().hex}",
        sender_agent_id=sender_id,
        receiver_agent_id=receiver_id,
        group_id=group_id,
        content=content.strip(),
        is_read=False,
        is_deleted=False,
        created_at=datetime.now(UTC)
    )

    db.add(message)
    db.commit()
    db.refresh(message)
    return message


async def get_chat_history(
    db: Session,
    user1_id: str,
    user2_id: str,
    skip: int = 0,
    limit: int = 50,
    before: Optional[datetime] = None
) -> List[ChatMessage]:
    """
    获取两个用户之间的聊天历史

    Args:
        db: 数据库会话
        user1_id: 用户1 ID
        user2_id: 用户2 ID
        skip: 跳过数量
        limit: 返回数量
        before: 只返回此时间之前的消息

    Returns:
        List[ChatMessage]: 消息列表（按时间倒序）
    """
    query = db.query(ChatMessage).filter(
        ChatMessage.group_id.is_(None),  # 非群聊
        (
            ((ChatMessage.sender_agent_id == user1_id) &
             (ChatMessage.receiver_agent_id == user2_id)) |
            ((ChatMessage.sender_agent_id == user2_id) &
             (ChatMessage.receiver_agent_id == user1_id))
        ),
        ChatMessage.is_deleted == False
    )

    if before:
        query = query.filter(ChatMessage.created_at < before)

    messages = query.order_by(
        ChatMessage.created_at.desc()
    ).offset(skip).limit(limit).all()

    return messages


async def mark_as_read(
    db: Session,
    message_id: str,
    reader_id: str
) -> bool:
    """
    标记消息为已读

    Args:
        db: 数据库会话
        message_id: 消息ID
        reader_id: 阅读者ID

    Returns:
        bool: 是否成功标记
    """
    message = db.query(ChatMessage).filter(
        ChatMessage.message_id == message_id,
        ChatMessage.is_deleted == False
    ).first()

    if not message:
        return False

    # 只有接收者可以标记为已读
    if message.receiver_agent_id != reader_id:
        return False

    message.is_read = True
    db.commit()
    return True


async def get_unread_count(
    db: Session,
    user_id: str
) -> int:
    """
    获取用户的未读消息数量

    Args:
        db: 数据库会话
        user_id: 用户ID

    Returns:
        int: 未读消息数量
    """
    count = db.query(ChatMessage).filter(
        ChatMessage.receiver_agent_id == user_id,
        ChatMessage.is_read == False,
        ChatMessage.is_deleted == False
    ).count()

    return count


async def delete_message(
    db: Session,
    message_id: str,
    user_id: str
) -> bool:
    """
    删除消息（软删除）

    Args:
        db: 数据库会话
        message_id: 消息ID
        user_id: 操作者ID

    Returns:
        bool: 是否成功删除
    """
    message = db.query(ChatMessage).filter(
        ChatMessage.message_id == message_id,
        ChatMessage.is_deleted == False
    ).first()

    if not message:
        return False

    # 只有发送者可以删除消息
    if message.sender_agent_id != user_id:
        return False

    message.is_deleted = True
    db.commit()
    return True


async def create_group_chat(
    db: Session,
    name: str,
    creator_id: str,
    member_ids: List[str]
) -> GroupChat:
    """
    创建群聊

    Args:
        db: 数据库会话
        name: 群名称
        creator_id: 创建者ID
        member_ids: 成员ID列表

    Returns:
        GroupChat: 创建的群聊对象
    """
    group = GroupChat(
        group_id=f"group_{uuid.uuid4().hex}",
        name=name,
        creator_agent_id=creator_id,
        is_public=True,
        is_deleted=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )

    db.add(group)

    # 添加创建者为成员
    creator_member = GroupChatMember(
        group_id=group.group_id,
        agent_id=creator_id,
        joined_at=datetime.now(UTC)
    )
    db.add(creator_member)

    # 添加其他成员
    for member_id in member_ids:
        if member_id != creator_id:
            member = GroupChatMember(
                group_id=group.group_id,
                agent_id=member_id,
                joined_at=datetime.now(UTC)
            )
            db.add(member)

    db.commit()
    db.refresh(group)
    return group


async def get_group_chat_messages(
    db: Session,
    group_id: str,
    skip: int = 0,
    limit: int = 50
) -> List[ChatMessage]:
    """
    获取群聊消息历史

    Args:
        db: 数据库会话
        group_id: 群聊ID
        skip: 跳过数量
        limit: 返回数量

    Returns:
        List[ChatMessage]: 消息列表
    """
    messages = db.query(ChatMessage).filter(
        ChatMessage.group_id == group_id,
        ChatMessage.is_deleted == False
    ).order_by(
        ChatMessage.created_at.desc()
    ).offset(skip).limit(limit).all()

    return messages


async def get_user_groups(
    db: Session,
    user_id: str
) -> List[GroupChat]:
    """
    获取用户加入的所有群聊

    Args:
        db: 数据库会话
        user_id: 用户ID

    Returns:
        List[GroupChat]: 群聊列表
    """
    memberships = db.query(GroupChatMember).filter(
        GroupChatMember.agent_id == user_id
    ).all()

    group_ids = [m.group_id for m in memberships]

    groups = db.query(GroupChat).filter(
        GroupChat.group_id.in_(group_ids),
        GroupChat.is_deleted == False
    ).all()

    return groups


async def get_chat_sessions(
    db: Session,
    user_id: str,
    limit: int = 50
) -> dict:
    """
    获取用户的所有聊天会话（一对一 + 群聊）

    Args:
        db: 数据库会话
        user_id: 用户ID
        limit: 返回数量

    Returns:
        dict: 包含 private_chats（一对一）和 group_chats（群聊）的字典
    """
    # ========== 获取一对一聊天会话 ==========
    # 查询用户作为发送者的所有消息（接收者非空）
    private_messages = db.query(ChatMessage).filter(
        ChatMessage.sender_agent_id == user_id,
        ChatMessage.receiver_agent_id.isnot(None),
        ChatMessage.group_id.is_(None),
        ChatMessage.is_deleted == False
    ).all()

    # 查询用户作为接收者的所有消息
    received_messages = db.query(ChatMessage).filter(
        ChatMessage.receiver_agent_id == user_id,
        ChatMessage.group_id.is_(None),
        ChatMessage.is_deleted == False
    ).all()

    # 合并所有消息
    all_private_messages = private_messages + received_messages

    # 提取唯一的聊天对象
    chat_partners = {}
    for msg in all_private_messages:
        partner_id = msg.receiver_agent_id if msg.sender_agent_id == user_id else msg.sender_agent_id
        if partner_id:
            # 获取最后一条消息时间
            if partner_id not in chat_partners or msg.created_at > chat_partners[partner_id]['last_message_at']:
                chat_partners[partner_id] = {
                    'partner_id': partner_id,
                    'last_message_at': msg.created_at,
                    'last_message': msg.content[:50] if msg.content else None
                }

    # 获取对方用户信息
    partner_ids = list(chat_partners.keys())
    if partner_ids:
        partners = db.query(ConnectedAgent).filter(
            ConnectedAgent.agent_id.in_(partner_ids)
        ).all()

        partner_map = {p.agent_id: p for p in partners}

        # 计算未读消息数
        for partner_id in chat_partners:
            unread_count = db.query(ChatMessage).filter(
                ChatMessage.sender_agent_id == partner_id,
                ChatMessage.receiver_agent_id == user_id,
                ChatMessage.is_read == False,
                ChatMessage.is_deleted == False
            ).count()

            partner = partner_map.get(partner_id)
            if partner:
                chat_partners[partner_id]['partner_name'] = partner.name
                chat_partners[partner_id]['partner_avatar'] = None
                chat_partners[partner_id]['unread_count'] = unread_count

    # ========== 获取群聊会话 ==========
    # 查询用户加入的所有群聊
    memberships = db.query(GroupChatMember).filter(
        GroupChatMember.agent_id == user_id
    ).all()

    group_ids = [m.group_id for m in memberships]

    groups = db.query(GroupChat).filter(
        GroupChat.group_id.in_(group_ids),
        GroupChat.is_deleted == False
    ).all()

    group_sessions = []
    for group in groups:
        # 获取群聊最后一条消息
        last_message = db.query(ChatMessage).filter(
            ChatMessage.group_id == group.group_id,
            ChatMessage.is_deleted == False
        ).order_by(
            ChatMessage.created_at.desc()
        ).first()

        # 获取群聊成员数
        member_count = db.query(GroupChatMember).filter(
            GroupChatMember.group_id == group.group_id
        ).count()

        group_sessions.append({
            'group_id': group.group_id,
            'group_name': group.name,
            'member_count': member_count,
            'last_message': last_message.content[:50] if last_message and last_message.content else None,
            'last_message_at': last_message.created_at if last_message else None,
            'created_by': group.created_by,
            'created_at': group.created_at
        })

    return {
        'private_chats': list(chat_partners.values()),
        'group_chats': group_sessions
    }
