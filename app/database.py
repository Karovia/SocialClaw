"""
数据库配置和会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from contextlib import contextmanager

from app.core.config import settings

# 创建 SQLAlchemy 引擎
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite 需要
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 数据库基类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话（用于 FastAPI 依赖注入）

    使用方式：
    ```python
    from fastapi import Depends
    from app.database import get_db

    @router.get("/users")
    async def get_users(db: Session = Depends(get_db)):
        users = db.query(User).all()
        return users
    ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """
    获取数据库会话（用于非 FastAPI 场景，如脚本）

    使用方式：
    ```python
    from app.database import get_db_session

    with get_db_session() as db:
        users = db.query(User).all()
    ```
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    初始化数据库（创建所有表）

    使用方式：
    ```bash
    python -c "from app.database import init_db; init_db()"
    ```
    """
    # 导入所有模型以确保它们被注册
    from app.models import user, second_me_binding, connected_agent, post, comment, chat_message, friendship, group_chat, activity_log

    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")


def drop_db():
    """
    删除所有数据库表（谨慎使用）
    """
    Base.metadata.drop_all(bind=engine)
    print("Database tables dropped")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "init":
            init_db()
        elif sys.argv[1] == "drop":
            drop_db()
        elif sys.argv[1] == "reset":
            drop_db()
            init_db()
    else:
        print("Usage: python app/database.py [init|drop|reset]")
