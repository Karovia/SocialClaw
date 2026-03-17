import pytest
from sqlalchemy.orm import Session
from app.models.friendship import Friendship, FriendshipStatus
from app.models.connected_agent import ConnectedAgent
from app.services.friend_service import (
    send_friend_request,
    accept_friend_request,
    reject_friend_request,
    get_friends_list,
    delete_friend,
    get_pending_requests,
)


def test_send_friend_request(db: Session):
    """测试发送好友请求"""
    # 创建两个测试 agent
    agent1 = ConnectedAgent(
        agent_id="agent_1",
        user_id="user_1",
        name="Agent One",
        description="Test agent 1"
    )
    agent2 = ConnectedAgent(
        agent_id="agent_2",
        user_id="user_2",
        name="Agent Two",
        description="Test agent 2"
    )
    db.add(agent1)
    db.add(agent2)
    db.commit()

    # 发送好友请求
    friendship = send_friend_request(db, "agent_1", "agent_2")

    assert friendship is not None
    assert friendship.agent_id_1 == "agent_1"
    assert friendship.agent_id_2 == "agent_2"
    assert friendship.status == FriendshipStatus.PENDING


def test_send_friend_request_duplicate(db: Session):
    """测试重复发送好友请求应该失败"""
    agent1 = ConnectedAgent(agent_id="agent_1_dup", user_id="user_1", name="Agent One", description="Test")
    agent2 = ConnectedAgent(agent_id="agent_2_dup", user_id="user_2", name="Agent Two", description="Test")
    db.add(agent1)
    db.add(agent2)
    db.commit()

    # 第一次发送
    send_friend_request(db, "agent_1_dup", "agent_2_dup")

    # 第二次发送应该抛出异常
    with pytest.raises(ValueError, match="好友关系已存在"):
        send_friend_request(db, "agent_1_dup", "agent_2_dup")


def test_accept_friend_request(db: Session):
    """测试接受好友请求"""
    agent1 = ConnectedAgent(agent_id="agent_accept_1", user_id="user_1", name="Agent One", description="Test")
    agent2 = ConnectedAgent(agent_id="agent_accept_2", user_id="user_2", name="Agent Two", description="Test")
    db.add(agent1)
    db.add(agent2)
    db.commit()

    friendship = send_friend_request(db, "agent_accept_1", "agent_accept_2")
    success = accept_friend_request(db, "agent_accept_2", friendship.friendship_id)

    assert success is True
    updated = db.query(Friendship).filter(Friendship.friendship_id == friendship.friendship_id).first()
    assert updated.status == FriendshipStatus.ACCEPTED


def test_reject_friend_request(db: Session):
    """测试拒绝好友请求"""
    agent1 = ConnectedAgent(agent_id="agent_reject_1", user_id="user_1", name="Agent One", description="Test")
    agent2 = ConnectedAgent(agent_id="agent_reject_2", user_id="user_2", name="Agent Two", description="Test")
    db.add(agent1)
    db.add(agent2)
    db.commit()

    friendship = send_friend_request(db, "agent_reject_1", "agent_reject_2")
    success = reject_friend_request(db, "agent_reject_2", friendship.friendship_id)

    assert success is True
    updated = db.query(Friendship).filter(Friendship.friendship_id == friendship.friendship_id).first()
    assert updated.status == FriendshipStatus.REJECTED


def test_get_friends_list(db: Session):
    """测试获取好友列表"""
    agent1 = ConnectedAgent(agent_id="agent_list_1", user_id="user_1", name="Agent One", description="Test")
    agent2 = ConnectedAgent(agent_id="agent_list_2", user_id="user_2", name="Agent Two", description="Test")
    agent3 = ConnectedAgent(agent_id="agent_list_3", user_id="user_3", name="Agent Three", description="Test")
    db.add_all([agent1, agent2, agent3])
    db.commit()

    # 1 -> 2 请求，接受
    f1 = send_friend_request(db, "agent_list_1", "agent_list_2")
    accept_friend_request(db, "agent_list_2", f1.friendship_id)

    # 1 -> 3 请求，待处理
    send_friend_request(db, "agent_list_1", "agent_list_3")

    # 获取已接受的好友列表
    friends = get_friends_list(db, "agent_list_1", FriendshipStatus.ACCEPTED)
    assert len(friends) == 1
    assert friends[0].agent_id == "agent_list_2"
