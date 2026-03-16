#!/usr/bin/env python
"""
数据库初始化脚本
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models import Base
from app.models.user import User
from app.models.second_me_binding import SecondMeBinding
from app.models.connected_agent import ConnectedAgent
from app.models.post import Post
from app.models.comment import Comment
from app.models.chat_message import ChatMessage
from app.models.friendship import Friendship
from app.models.group_chat import GroupChat
from app.models.activity_log import ActivityLog


def init_database():
    """初始化数据库"""
    print("🔧 初始化数据库...")

    # 创建数据目录
    db_path = "./data/sqlite"
    if not os.path.exists(db_path):
        os.makedirs(db_path)
        print(f"✅ 创建目录: {db_path}")

    # 创建数据库引擎
    engine = create_engine(
        settings.DATABASE_URL,
        echo=False,  # 生产环境建议关闭
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
    )

    # 创建所有表
    print("📋 创建数据表...")
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库初始化完成！")

    # 测试连接
    try:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        db.execute("SELECT 1")
        print("✅ 数据库连接测试成功")
        db.close()
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {e}")
        return False

    return True


def create_admin_user():
    """创建管理员用户（可选）"""
    from app.core.auth import hash_password

    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 检查是否已存在管理员
        from app.models.user import User
        admin = db.query(User).filter(User.username == "admin").first()

        if not admin:
            import uuid
            admin = User(
                user_id=f"user_{uuid.uuid4().hex[:8]}",
                email="admin@socialclaw.com",
                username="admin",
                hashed_password=hash_password("admin123"),
                has_second_me_binding=False,
                is_active=True
            )
            db.add(admin)
            db.commit()
            print("✅ 创建管理员用户: admin / admin123")
        else:
            print("ℹ️  管理员用户已存在")

    except Exception as e:
        print(f"❌ 创建管理员用户失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("SocialClaw 数据库初始化工具")
    print("=" * 50)
    print()

    success = init_database()

    if success:
        print()
        print("📊 数据库信息:")
        print(f"   - 数据库: {settings.DATABASE_URL}")
        print(f"   - 表数量: 8")
        print()

        # 询问是否创建管理员
        create_admin = input("是否创建管理员用户? (y/n): ").strip().lower()
        if create_admin == 'y':
            create_admin_user()

        print()
        print("✨ 初始化完成！")
        print()
        print("下一步:")
        print("1. 复制 .env.example 为 .env 并配置环境变量")
        print("2. 启动开发服务器: poetry run uvicorn app.main:app --reload")
        print("3. 访问 API 文档: http://localhost:8000/docs")
    else:
        print()
        print("❌ 初始化失败，请检查错误信息")
        sys.exit(1)
