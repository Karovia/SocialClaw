"""
数据库迁移：添加 Agent 自主行为相关表和字段
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import engine, Base
from app.models.agent_autonomy_log import AgentAutonomyLog
from app.models.connected_agent import ConnectedAgent
from sqlalchemy import inspect, text


def migrate():
    """执行迁移"""
    print("Starting database migration for Agent Autonomy...")

    # 创建新表
    inspector = inspect(engine)

    # 检查 agent_autonomy_logs 表是否存在
    if "agent_autonomy_logs" not in inspector.get_table_names():
        print("Creating agent_autonomy_logs table...")
        AgentAutonomyLog.__table__.create(engine)
        print("[OK] agent_autonomy_logs table created")
    else:
        print("[OK] agent_autonomy_logs table already exists")

    # 检查 connected_agents 表是否需要添加新字段
    columns = [col["name"] for col in inspector.get_columns("connected_agents")]

    with engine.connect() as conn:
        # 添加 auto_post_enabled
        if "auto_post_enabled" not in columns:
            print("Adding auto_post_enabled column...")
            conn.execute(text(
                "ALTER TABLE connected_agents ADD COLUMN auto_post_enabled BOOLEAN DEFAULT TRUE"
            ))
            conn.commit()
            print("[OK] auto_post_enabled column added")

        # 添加 auto_friend_enabled
        if "auto_friend_enabled" not in columns:
            print("Adding auto_friend_enabled column...")
            conn.execute(text(
                "ALTER TABLE connected_agents ADD COLUMN auto_friend_enabled BOOLEAN DEFAULT TRUE"
            ))
            conn.commit()
            print("[OK] auto_friend_enabled column added")

        # 添加 post_interval_hours
        if "post_interval_hours" not in columns:
            print("Adding post_interval_hours column...")
            conn.execute(text(
                "ALTER TABLE connected_agents ADD COLUMN post_interval_hours INTEGER DEFAULT 24"
            ))
            conn.commit()
            print("[OK] post_interval_hours column added")

        # 添加 friend_request_limit_per_day
        if "friend_request_limit_per_day" not in columns:
            print("Adding friend_request_limit_per_day column...")
            conn.execute(text(
                "ALTER TABLE connected_agents ADD COLUMN friend_request_limit_per_day INTEGER DEFAULT 5"
            ))
            conn.commit()
            print("[OK] friend_request_limit_per_day column added")

        # 添加 max_friends
        if "max_friends" not in columns:
            print("Adding max_friends column...")
            conn.execute(text(
                "ALTER TABLE connected_agents ADD COLUMN max_friends INTEGER DEFAULT 100"
            ))
            conn.commit()
            print("[OK] max_friends column added")

    print("\n[OK] Database migration completed!")


if __name__ == "__main__":
    migrate()