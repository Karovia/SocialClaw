"""
帖子服务层测试
"""
import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.connected_agent import ConnectedAgent
from app.schemas.post import PostCreate


@pytest.fixture
def setup_user_and_agent(db):
    """创建测试用户和 Agent"""
    user = User(
        user_id="soc_user_test123",
        email="test@example.com",
        username="testuser",
        hashed_password=None,
        has_second_me_binding=True,
        is_active=True
    )
    db.add(user)

    agent = ConnectedAgent(
        agent_id="soc_user_test123",
        user_id=user.user_id,
        name="Test Agent",
        description="Test agent for testing"
    )
    db.add(agent)
    db.commit()

    return user, agent


class TestCreatePost:
    """测试创建帖子"""

    def test_create_post(self, db, setup_user_and_agent):
        """测试创建帖子"""
        from app.services.post_service import create_post

        user, agent = setup_user_and_agent
        post_data = PostCreate(
            content="这是我的第一个帖子 #技术转行",
            topic="技术转行"
        )

        post = create_post(db, agent.agent_id, post_data)

        assert post.content == "这是我的第一个帖子 #技术转行"
        assert post.topic == "技术转行"
        assert post.likes_count == 0
        assert post.comments_count == 0
        assert post.is_deleted == False
        assert post.agent_id == agent.agent_id


class TestGetPostList:
    """测试获取帖子列表"""

    def test_get_post_list(self, db, setup_user_and_agent):
        """测试获取帖子列表"""
        from app.services.post_service import create_post, get_post_list

        user, agent = setup_user_and_agent
        # 创建测试数据
        post1 = create_post(db, agent.agent_id, PostCreate(content="帖子 1", topic="技术转行"))
        post2 = create_post(db, agent.agent_id, PostCreate(content="帖子 2", topic="职场"))
        post3 = create_post(db, agent.agent_id, PostCreate(content="帖子 3", topic="技术转行"))

        # 测试获取全部
        posts = get_post_list(db, skip=0, limit=10)
        assert len(posts) >= 3

        # 测试分页
        posts_page1 = get_post_list(db, skip=0, limit=2)
        posts_page2 = get_post_list(db, skip=2, limit=2)
        assert len(posts_page1) == 2
        assert posts_page1[0].post_id != posts_page2[0].post_id

        # 测试按话题过滤
        tech_posts = get_post_list(db, topic="技术转行")
        assert len(tech_posts) == 2
        assert all(p.topic == "技术转行" for p in tech_posts)


class TestGetPostById:
    """测试获取帖子详情"""

    def test_get_post_by_id(self, db, setup_user_and_agent):
        """测试获取帖子详情"""
        from app.services.post_service import create_post, get_post_by_id

        user, agent = setup_user_and_agent
        post = create_post(db, agent.agent_id, PostCreate(content="测试帖子", topic="技术转行"))

        # 测试正常获取
        fetched = get_post_by_id(db, post.post_id)
        assert fetched is not None
        assert fetched.post_id == post.post_id
        assert fetched.content == "测试帖子"

        # 测试不存在的帖子
        not_found = get_post_by_id(db, "post_nonexistent")
        assert not_found is None

        # 测试已删除的帖子（软删除后应返回 None）
        post.is_deleted = True
        db.commit()
        deleted_fetch = get_post_by_id(db, post.post_id)
        assert deleted_fetch is None


class TestUpdatePost:
    """测试编辑帖子"""

    def test_update_post(self, db, setup_user_and_agent):
        """测试编辑帖子"""
        from app.services.post_service import create_post, update_post

        user, agent = setup_user_and_agent
        post = create_post(db, agent.agent_id, PostCreate(content="原始内容", topic="技术转行"))

        # 测试正常更新
        updated = update_post(db, post.post_id, agent.agent_id, {
            "content": "更新后的内容",
            "topic": "职场"
        })

        assert updated is not None
        assert updated.content == "更新后的内容"
        assert updated.topic == "职场"

        # 测试更新不存在的帖子
        not_found = update_post(db, "post_nonexistent", agent.agent_id, {"content": "x"})
        assert not_found is None

        # 测试更新他人的帖子（权限检查）- 需要另一个用户
        other_agent = ConnectedAgent(
            agent_id="soc_user_other",
            user_id="soc_user_other",
            name="Other Agent",
            description="Other agent"
        )
        db.add(other_agent)
        db.commit()

        unauth = update_post(db, post.post_id, other_agent.agent_id, {"content": "x"})
        assert unauth is None  # 无权限返回 None


class TestDeletePost:
    """测试删除帖子"""

    def test_delete_post(self, db, setup_user_and_agent):
        """测试删除帖子（软删除）"""
        from app.services.post_service import create_post, delete_post, get_post_by_id

        user, agent = setup_user_and_agent
        post = create_post(db, agent.agent_id, PostCreate(content="要删除的帖子", topic="技术转行"))

        # 测试正常删除
        result = delete_post(db, post.post_id, agent.agent_id)
        assert result == True

        # 验证软删除标志
        db.refresh(post)
        assert post.is_deleted == True

        # 验证删除后无法获取
        fetched = get_post_by_id(db, post.post_id)
        assert fetched is None

        # 测试删除不存在的帖子
        result2 = delete_post(db, "post_nonexistent", agent.agent_id)
        assert result2 == False

        # 测试删除他人的帖子
        post2 = create_post(db, agent.agent_id, PostCreate(content="帖子 2", topic="技术转行"))
        other_agent = ConnectedAgent(
            agent_id="soc_user_other",
            user_id="soc_user_other",
            name="Other Agent",
            description="Other agent"
        )
        db.add(other_agent)
        db.commit()

        result3 = delete_post(db, post2.post_id, other_agent.agent_id)
        assert result3 == False
