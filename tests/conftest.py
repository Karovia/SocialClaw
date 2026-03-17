"""
测试配置和 fixture
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db
from app.models import Base

# 导入所有模型以注册到 Base
from app.models.user import User
from app.models.connected_agent import ConnectedAgent
from app.models.post import Post
from app.models.comment import Comment
from app.models.chat_message import ChatMessage
from app.models.friendship import Friendship
from app.models.group_chat import GroupChat
from app.models.activity_log import ActivityLog
from app.models.second_me_binding import SecondMeBinding
from app.models.like import PostLike, CommentLike


# 使用内存 SQLite 进行测试
SQLITE_TEST_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLITE_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def db_engine():
    """创建测试数据库引擎"""
    # 创建所有表
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    # 清理
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db(db_engine):
    """每个测试函数一个独立的数据库会话"""
    # 每次测试前重新创建所有表
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    # 创建新的事务
    connection = db_engine.connect()
    transaction = connection.begin()

    # 创建会话
    session = TestSessionLocal(bind=connection)

    try:
        yield session
    finally:
        # 回滚事务，清理数据
        transaction.rollback()
        session.close()
        connection.close()


@pytest.fixture(scope="function")
def client(db):
    """测试客户端，注入测试数据库"""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db):
    """创建测试用户"""
    user = User(
        user_id="soc_user_test123",
        email="test@example.com",
        username="testuser",
        hashed_password=None,
        has_second_me_binding=True,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_agent(db, test_user):
    """创建测试 Agent"""
    agent = ConnectedAgent(
        agent_id="soc_user_test123",  # 使用相同的 ID 作为默认 agent
        user_id=test_user.user_id,
        name="Test Agent",
        description="Test agent for testing"
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@pytest.fixture(scope="function")
def auth_headers(client, test_user):
    """生成带认证的请求头"""
    from app.core.auth import create_access_token
    from datetime import timedelta

    token = create_access_token(
        data={"user_id": test_user.user_id},
        expires_delta=timedelta(hours=1)
    )

    return {"Authorization": f"Bearer {token}"}
