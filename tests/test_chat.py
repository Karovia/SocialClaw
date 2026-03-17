"""
聊天系统测试模块
测试聊天服务和 API 端点
"""
import pytest
from datetime import datetime, UTC, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

# 导入要测试的模块
from app.services.chat_service import (
    send_message,
    get_chat_history,
    mark_as_read,
    get_unread_count,
    delete_message,
    create_group_chat,
    get_group_chat_messages,
    get_user_groups
)


# ============= Test Fixtures =============

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = Mock(spec=Session)
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    return db


@pytest.fixture
def sample_user_id():
    """示例用户ID"""
    return "soc_user_12345"


@pytest.fixture
def another_user_id():
    """另一个示例用户ID"""
    return "soc_user_67890"


# ============= Service Layer Tests =============

class TestChatService:
    """聊天服务测试"""

    @pytest.mark.asyncio
    async def test_send_one_to_one_message(self, mock_db, sample_user_id, another_user_id):
        """测试发送一对一消息"""
        # 执行
        message = await send_message(
            db=mock_db,
            sender_id=sample_user_id,
            receiver_id=another_user_id,
            content="你好！"
        )

        # 验证
        assert message is not None
        assert message.message_id.startswith("msg_")
        assert message.sender_agent_id == sample_user_id
        assert message.receiver_agent_id == another_user_id
        assert message.content == "你好！"
        assert message.is_read is False
        assert message.group_id is None

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_empty_content_raises_error(
        self, mock_db, sample_user_id, another_user_id
    ):
        """测试发送空消息会抛出错误"""
        with pytest.raises(ValueError, match="消息内容不能为空"):
            await send_message(
                db=mock_db,
                sender_id=sample_user_id,
                receiver_id=another_user_id,
                content=""
            )

    @pytest.mark.asyncio
    async def test_send_message_no_receiver_or_group_raises_error(
        self, mock_db, sample_user_id
    ):
        """测试不提供接收者或群聊ID会抛出错误"""
        with pytest.raises(ValueError, match="必须提供 receiver_id"):
            await send_message(
                db=mock_db,
                sender_id=sample_user_id,
                content="你好"
            )

    @pytest.mark.asyncio
    async def test_send_group_message(self, mock_db, sample_user_id):
        """测试发送群聊消息"""
        group_id = "group_abc123"

        message = await send_message(
            db=mock_db,
            sender_id=sample_user_id,
            group_id=group_id,
            content="大家好！"
        )

        assert message is not None
        assert message.group_id == group_id
        assert message.receiver_agent_id is None
        assert message.content == "大家好！"

    @pytest.mark.asyncio
    async def test_get_chat_history(self, mock_db, sample_user_id, another_user_id):
        """测试获取聊天历史"""
        # 模拟查询结果
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [
            Mock(
                message_id="msg_1",
                sender_agent_id=sample_user_id,
                receiver_agent_id=another_user_id,
                content="你好",
                created_at=datetime.now(UTC)
            )
        ]
        mock_db.query.return_value = mock_query

        # 执行
        messages = await get_chat_history(
            db=mock_db,
            user1_id=sample_user_id,
            user2_id=another_user_id
        )

        # 验证
        assert len(messages) == 1
        mock_db.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_as_read(self, mock_db, sample_user_id, another_user_id):
        """测试标记消息为已读"""
        # 模拟消息
        mock_message = Mock()
        mock_message.receiver_agent_id = sample_user_id
        mock_message.is_read = False

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_message
        mock_db.query.return_value = mock_query

        # 执行
        success = await mark_as_read(
            db=mock_db,
            message_id="msg_1",
            reader_id=sample_user_id
        )

        # 验证
        assert success is True
        assert mock_message.is_read is True
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_as_read_wrong_user_fails(
        self, mock_db, sample_user_id, another_user_id
    ):
        """测试非接收者无法标记消息为已读"""
        mock_message = Mock()
        mock_message.receiver_agent_id = another_user_id  # 不是当前用户

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_message
        mock_db.query.return_value = mock_query

        success = await mark_as_read(
            db=mock_db,
            message_id="msg_1",
            reader_id=sample_user_id
        )

        assert success is False

    @pytest.mark.asyncio
    async def test_get_unread_count(self, mock_db, sample_user_id):
        """测试获取未读消息数量"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_db.query.return_value = mock_query

        count = await get_unread_count(db=mock_db, user_id=sample_user_id)

        assert count == 5

    @pytest.mark.asyncio
    async def test_delete_message(self, mock_db, sample_user_id):
        """测试删除消息"""
        mock_message = Mock()
        mock_message.sender_agent_id = sample_user_id
        mock_message.is_deleted = False

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_message
        mock_db.query.return_value = mock_query

        success = await delete_message(
            db=mock_db,
            message_id="msg_1",
            user_id=sample_user_id
        )

        assert success is True
        assert mock_message.is_deleted is True

    @pytest.mark.asyncio
    async def test_create_group_chat(self, mock_db, sample_user_id):
        """测试创建群聊"""
        member_ids = ["user_1", "user_2", "user_3"]

        group = await create_group_chat(
            db=mock_db,
            name="技术讨论群",
            creator_id=sample_user_id,
            member_ids=member_ids
        )

        assert group is not None
        assert group.group_id.startswith("group_")
        assert group.name == "技术讨论群"
        assert group.created_by == sample_user_id

    @pytest.mark.asyncio
    async def test_get_user_groups(self, mock_db, sample_user_id):
        """测试获取用户的群聊列表"""
        mock_membership = Mock()
        mock_membership.group_id = "group_1"

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_membership]
        mock_db.query.return_value = mock_query

        # 模拟群查询
        mock_group = Mock()
        mock_group.group_id = "group_1"
        mock_group.name = "测试群"

        mock_group_query = Mock()
        mock_group_query.filter.return_value = mock_group_query
        mock_group_query.all.return_value = [mock_group]

        # 让第二次 query 返回群查询
        mock_db.query.side_effect = [mock_query, mock_group_query]

        groups = await get_user_groups(db=mock_db, user_id=sample_user_id)

        assert len(groups) == 1


# ============= API Layer Tests =============

class TestChatAPI:
    """聊天 API 测试（使用 FastAPI TestClient）"""

    def test_send_message_endpoint_schema(self):
        """测试发送消息请求的 Schema"""
        from app.api.v1.chat import MessageSendRequest

        # 验证一对一消息
        request = MessageSendRequest(
            receiver_id="user_1",
            content="你好"
        )
        assert request.receiver_id == "user_1"
        assert request.content == "你好"

        # 验证群聊消息
        request = MessageSendRequest(
            group_id="group_1",
            content="大家好"
        )
        assert request.group_id == "group_1"

    def test_group_create_request_schema(self):
        """测试创建群聊请求的 Schema"""
        from app.api.v1.chat import GroupCreateRequest

        request = GroupCreateRequest(
            name="测试群",
            member_ids=["user_1", "user_2"]
        )
        assert request.name == "测试群"
        assert len(request.member_ids) == 2

    def test_api_response_schema(self):
        """测试 API 响应 Schema"""
        from app.api.v1.chat import ApiResponse

        response = ApiResponse(
            code=0,
            message="成功",
            data={"key": "value"}
        )
        assert response.code == 0
        assert response.message == "成功"
        assert response.data == {"key": "value"}


# ============= Integration Tests =============

class TestChatIntegration:
    """聊天系统集成测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_chat_flow(self, mock_db):
        """测试完整的聊天流程"""
        user1 = "user_1"
        user2 = "user_2"

        # 1. 用户1发送消息给用户2
        msg1 = await send_message(
            db=mock_db,
            sender_id=user1,
            receiver_id=user2,
            content="你好！"
        )

        # 2. 用户2回复
        msg2 = await send_message(
            db=mock_db,
            sender_id=user2,
            receiver_id=user1,
            content="你好，有什么事吗？"
        )

        # 3. 获取聊天历史
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [msg1, msg2]
        mock_db.query.return_value = mock_query

        history = await get_chat_history(
            db=mock_db,
            user1_id=user1,
            user2_id=user2
        )

        assert len(history) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
