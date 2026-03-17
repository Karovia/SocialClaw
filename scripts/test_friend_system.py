"""
模块三好友系统功能演示脚本

演示好友系统的核心功能：
1. 发送好友请求
2. 接受/拒绝好友请求
3. 查看好友列表
4. 获取推荐好友
"""

from sqlalchemy.orm import Session
from app.models.user import User
from app.models.connected_agent import ConnectedAgent
from app.services.friend_service import (
    send_friend_request,
    accept_friend_request,
    reject_friend_request,
    get_friends_list,
    delete_friend,
    get_recommended_friends,
    get_pending_requests
)
from app.models.friendship import FriendshipStatus


def setup_test_data(db: Session):
    """创建测试数据"""
    print("=" * 60)
    print("步骤 1: 创建测试用户和 Agent")
    print("=" * 60)

    # 创建两个测试用户
    user1 = User(
        user_id="soc_user_test1",
        second_me_user_id="labs_user_001",
        email="user1@example.com",
        username="测试用户1",
        avatar_url="https://example.com/avatar1.jpg"
    )
    user2 = User(
        user_id="soc_user_test2",
        second_me_user_id="labs_user_002",
        email="user2@example.com",
        username="测试用户2",
        avatar_url="https://example.com/avatar2.jpg"
    )
    user3 = User(
        user_id="soc_user_test3",
        second_me_user_id="labs_user_003",
        email="user3@example.com",
        username="测试用户3",
        avatar_url="https://example.com/avatar3.jpg"
    )

    db.add_all([user1, user2, user3])
    db.commit()

    # 创建对应的 Agent
    agent1 = ConnectedAgent(
        agent_id="agent_001",
        user_id="soc_user_test1",
        name="Agent One",
        description="第一个测试 Agent",
        interests='["编程", "读书", "旅行"]',
        autonomy_level="80",
        is_active=True
    )
    agent2 = ConnectedAgent(
        agent_id="agent_002",
        user_id="soc_user_test2",
        name="Agent Two",
        description="第二个测试 Agent",
        interests='["编程", "音乐", "旅行"]',
        autonomy_level="90",
        is_active=True
    )
    agent3 = ConnectedAgent(
        agent_id="agent_003",
        user_id="soc_user_test3",
        name="Agent Three",
        description="第三个测试 Agent",
        interests='["读书", "电影", "美食"]',
        autonomy_level="70",
        is_active=True
    )

    db.add_all([agent1, agent2, agent3])
    db.commit()

    print(f"✓ 创建用户: {user1.username}, {user2.username}, {user3.username}")
    print(f"✓ 创建 Agent: {agent1.name}, {agent2.name}, {agent3.name}")
    print()

    return agent1, agent2, agent3


def test_send_friend_request(db: Session, sender, receiver):
    """测试发送好友请求"""
    print("=" * 60)
    print(f"步骤 2: {sender.name} 发送好友请求给 {receiver.name}")
    print("=" * 60)

    try:
        friendship = send_friend_request(db, sender.agent_id, receiver.agent_id)
        print(f"✓ 好友请求已发送!")
        print(f"  - Friendship ID: {friendship.friendship_id}")
        print(f"  - 状态: {friendship.status.value}")
        print(f"  - 发送方: {sender.name} ({sender.agent_id})")
        print(f"  - 接收方: {receiver.name} ({receiver.agent_id})")
        print()
        return friendship
    except ValueError as e:
        print(f"✗ 错误: {e}")
        print()
        return None


def test_accept_friend_request(db: Session, friendship, receiver_agent_id):
    """测试接受好友请求"""
    print("=" * 60)
    print(f"步骤 3: 接受好友请求")
    print("=" * 60)

    success = accept_friend_request(db, receiver_agent_id, friendship.friendship_id)

    if success:
        print(f"✓ 好友请求已接受!")
        friendship = db.query(friendship.__class__).filter(
            friendship.__class__.friendship_id == friendship.friendship_id
        ).first()
        print(f"  - 现在状态: {friendship.status.value}")
        print()
        return True
    else:
        print("✗ 接受失败")
        print()
        return False


def test_get_friends_list(db: Session, agent):
    """测试获取好友列表"""
    print("=" * 60)
    print(f"步骤 4: {agent.name} 查看好友列表")
    print("=" * 60)

    friends = get_friends_list(db, agent.agent_id)

    print(f"✓ 找到 {len(friends)} 个好友:")
    for friend in friends:
        print(f"  - {friend.name} (匹配度: {getattr(friend, 'match_score', 'N/A')})")
        print(f"    状态: {friend.status.value}")
    print()


def test_get_recommended_friends(db: Session, agent):
    """测试获取推荐好友"""
    print("=" * 60)
    print(f"步骤 5: {agent.name} 查看推荐好友")
    print("=" * 60)

    recommendations = get_recommended_friends(db, agent.agent_id, limit=3)

    print(f"✓ 基于兴趣找到 {len(recommendations)} 个推荐好友:")
    for rec in recommendations:
        print(f"  - {rec.name}")
        print(f"    兴趣: {', '.join(rec.interests)}")
        print(f"    匹配度: {rec.match_score:.2%}")
    print()


def test_reject_friend_request(db: Session, friendship, receiver_agent_id):
    """测试拒绝好友请求"""
    print("=" * 60)
    print(f"步骤 6: 拒绝好友请求")
    print("=" * 60)

    success = reject_friend_request(db, receiver_agent_id, friendship.friendship_id)

    if success:
        print(f"✓ 好友请求已拒绝!")
        friendship = db.query(friendship.__class__).filter(
            friendship.__class__.friendship_id == friendship.friendship_id
        ).first()
        print(f"  - 现在状态: {friendship.status.value}")
        print()
        return True
    else:
        print("✗ 拒绝失败")
        print()
        return False


def test_delete_friend(db: Session, friendship, user_agent_id):
    """测试删除好友"""
    print("=" * 60)
    print(f"步骤 7: 删除好友关系")
    print("=" * 60)

    success = delete_friend(db, user_agent_id, friendship.friendship_id)

    if success:
        print(f"✓ 好友关系已删除!")
        print()
        return True
    else:
        print("✗ 删除失败")
        print()
        return False


def run_demo():
    """运行完整演示"""
    from app.database import SessionLocal

    db = SessionLocal()

    try:
        print("\n" + "=" * 60)
        print(" " * 15 + "SocialClaw 好友系统演示")
        print("=" * 60 + "\n")

        # 步骤 1: 创建测试数据
        agent1, agent2, agent3 = setup_test_data(db)

        # 步骤 2: 发送好友请求
        friendship1 = test_send_friend_request(db, agent1, agent2)

        # 步骤 3: 接受好友请求
        if friendship1:
            test_accept_friend_request(db, friendship1, agent2.agent_id)

            # 步骤 4: 查看好友列表
            test_get_friends_list(db, agent1)
            test_get_friends_list(db, agent2)

        # 步骤 5: 查看推荐好友
        test_get_recommended_friends(db, agent1)

        # 测试拒绝功能（需要新的请求）
        print("=" * 60)
        print("测试拒绝功能")
        print("=" * 60)

        friendship2 = test_send_friend_request(db, agent1, agent3)
        if friendship2:
            test_reject_friend_request(db, friendship2, agent3.agent_id)

        print("\n" + "=" * 60)
        print(" " * 20 + "✨ 演示完成 ✨")
        print("=" * 60 + "\n")

    finally:
        db.close()


if __name__ == "__main__":
    run_demo()
