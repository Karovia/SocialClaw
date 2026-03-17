"""
聊天系统数据库迁移脚本
修复 chat_messages 和 group_chats 表结构，添加 group_chat_members 表

执行前请务必备份数据库！
"""
import sqlite3
import os
import shutil
from datetime import datetime


# 数据库路径
DB_PATH = "D:/SocialClaw/data/sqlite/socialclaw.db"
BACKUP_PATH = "D:/SocialClaw/data/sqlite/socialclaw_backup_{}.db".format(
    datetime.now().strftime("%Y%m%d_%H%M%S")
)


def backup_database():
    """备份数据库"""
    print(f"正在备份数据库到: {BACKUP_PATH}")
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print("[OK] 备份完成")


def check_existing_tables(conn):
    """检查现有表结构"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    print("\n现有表:")
    for table in tables:
        print(f"  - {table}")

    return tables


def migrate_chat_messages(conn):
    """迁移 chat_messages 表 - 修改 receiver_agent_id 为可空"""
    cursor = conn.cursor()

    print("\n检查 chat_messages 表...")
    cursor.execute("PRAGMA table_info(chat_messages)")
    columns = cursor.fetchall()

    receiver_nullable = None
    for col in columns:
        if col[1] == 'receiver_agent_id':
            # SQLite 中 nullable 不是直接可见的，但我们可以检查约束
            print(f"  receiver_agent_id 字段: {col}")

    # SQLite 不支持直接 ALTER TABLE MODIFY COLUMN
    # 我们需要重建表
    print("\n重建 chat_messages 表以支持群聊...")

    # 1. 重命名旧表
    cursor.execute("ALTER TABLE chat_messages RENAME TO chat_messages_old")

    # 2. 创建新表（receiver_agent_id 改为 nullable）
    cursor.execute("""
        CREATE TABLE chat_messages (
            message_id VARCHAR NOT NULL,
            sender_agent_id VARCHAR NOT NULL,
            receiver_agent_id VARCHAR,
            group_id VARCHAR,
            content TEXT NOT NULL,
            is_read BOOLEAN,
            is_deleted BOOLEAN,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            PRIMARY KEY (message_id),
            FOREIGN KEY(sender_agent_id) REFERENCES connected_agents (agent_id),
            FOREIGN KEY(receiver_agent_id) REFERENCES connected_agents (agent_id),
            FOREIGN KEY(group_id) REFERENCES group_chats (group_id)
        )
    """)

    # 3. 复制数据
    cursor.execute("""
        INSERT INTO chat_messages
        SELECT * FROM chat_messages_old
    """)

    # 4. 重建索引
    cursor.execute("CREATE INDEX ix_chat_messages_message_id ON chat_messages (message_id)")
    cursor.execute("CREATE INDEX ix_chat_messages_sender_agent_id ON chat_messages (sender_agent_id)")
    cursor.execute("CREATE INDEX ix_chat_messages_receiver_agent_id ON chat_messages (receiver_agent_id)")
    cursor.execute("CREATE INDEX ix_chat_messages_group_id ON chat_messages (group_id)")
    cursor.execute("CREATE INDEX ix_chat_messages_created_at ON chat_messages (created_at)")

    # 5. 删除旧表
    cursor.execute("DROP TABLE chat_messages_old")

    print("✓ chat_messages 表迁移完成")


def create_group_chat_members_table(conn):
    """创建 group_chat_members 关联表"""
    cursor = conn.cursor()

    # 检查表是否已存在
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='group_chat_members'
    """)

    if cursor.fetchone():
        print("\n✓ group_chat_members 表已存在，跳过创建")
        return

    print("\n创建 group_chat_members 表...")

    cursor.execute("""
        CREATE TABLE group_chat_members (
            group_id VARCHAR NOT NULL,
            agent_id VARCHAR NOT NULL,
            joined_at DATETIME NOT NULL,
            PRIMARY KEY (group_id, agent_id),
            FOREIGN KEY(group_id) REFERENCES group_chats (group_id),
            FOREIGN KEY(agent_id) REFERENCES connected_agents (agent_id)
        )
    """)

    cursor.execute("CREATE INDEX ix_group_chat_members_group_id ON group_chat_members (group_id)")
    cursor.execute("CREATE INDEX ix_group_chat_members_agent_id ON group_chat_members (agent_id)")

    print("✓ group_chat_members 表创建完成")


def migrate_group_chat_members(conn):
    """迁移现有群聊的成员数据"""
    cursor = conn.cursor()

    print("\n检查是否需要迁移群聊成员数据...")

    # 检查 group_chats 表是否有 members 列
    cursor.execute("PRAGMA table_info(group_chats)")
    columns = {col[1]: col for col in cursor.fetchall()}

    if 'members' not in columns:
        print("  group_chats 表没有 members 列，无需迁移")
        return

    print("  发现 members 列，开始迁移数据...")

    import json

    # 获取所有群聊及其成员
    cursor.execute("SELECT group_id, members FROM group_chats WHERE members IS NOT NULL")
    groups = cursor.fetchall()

    migrated_count = 0
    for group_id, members_json in groups:
        if not members_json:
            continue

        try:
            members = json.loads(members_json)
        except json.JSONDecodeError:
            print(f"  ⚠ 跳过无效的 JSON: group_id={group_id}")
            continue

        # 为每个成员创建关联记录
        for agent_id in members:
            if agent_id:  # 跳过空值
                cursor.execute("""
                    INSERT OR IGNORE INTO group_chat_members
                    (group_id, agent_id, joined_at)
                    VALUES (?, ?, ?)
                """, (group_id, agent_id, datetime.utcnow().isoformat()))
                migrated_count += 1

    print(f"✓ 已迁移 {migrated_count} 条群聊成员记录")


def update_group_chats_table(conn):
    """更新 group_chats 表 - 移除 members 列"""
    cursor = conn.cursor()

    print("\n更新 group_chats 表结构...")

    # 检查是否已有 is_deleted 列
    cursor.execute("PRAGMA table_info(group_chats)")
    columns = {col[1]: col for col in cursor.fetchall()}

    needs_migration = 'members' in columns or 'is_deleted' not in columns or 'updated_at' not in columns

    if not needs_migration:
        print("  group_chats 表结构已是最新，无需更新")
        return

    # 重建表
    print("  重建 group_chats 表...")

    # 1. 重命名旧表
    cursor.execute("ALTER TABLE group_chats RENAME TO group_chats_old")

    # 2. 创建新表
    cursor.execute("""
        CREATE TABLE group_chats (
            group_id VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            description TEXT,
            creator_agent_id VARCHAR NOT NULL,
            is_public BOOLEAN,
            is_deleted BOOLEAN,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            PRIMARY KEY (group_id),
            FOREIGN KEY(creator_agent_id) REFERENCES connected_agents (agent_id)
        )
    """)

    # 3. 复制数据（排除 members 列）
    if 'is_deleted' in columns and 'updated_at' in columns:
        cursor.execute("""
            INSERT INTO group_chats
            (group_id, name, description, creator_agent_id, is_public, is_deleted, created_at, updated_at)
            SELECT group_id, name, description, creator_agent_id, is_public, is_deleted, created_at, updated_at
            FROM group_chats_old
        """)
    elif 'is_deleted' in columns:
        cursor.execute("""
            INSERT INTO group_chats
            (group_id, name, description, creator_agent_id, is_public, is_deleted, created_at, updated_at)
            SELECT group_id, name, description, creator_agent_id, is_public, is_deleted, created_at, created_at
            FROM group_chats_old
        """)
    else:
        # 旧表没有 is_deleted，设置默认值
        cursor.execute("""
            INSERT INTO group_chats
            (group_id, name, description, creator_agent_id, is_public, is_deleted, created_at, updated_at)
            SELECT group_id, name, description, creator_agent_id, is_public, 0, created_at, created_at
            FROM group_chats_old
        """)

    # 4. 重建索引
    cursor.execute("CREATE INDEX ix_group_chats_group_id ON group_chats (group_id)")

    # 5. 删除旧表
    cursor.execute("DROP TABLE group_chats_old")

    print("✓ group_chats 表更新完成")


def verify_migration(conn):
    """验证迁移结果"""
    cursor = conn.cursor()

    print("\n=== 迁移验证 ===")

    # 检查表结构
    tables_to_check = ['chat_messages', 'group_chats', 'group_chat_members']

    for table in tables_to_check:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        print(f"\n{table} 表:")
        for col in columns:
            print(f"  {col[1]:25} {col[2]:15} {'NOT NULL' if col[3] else 'NULLABLE':10}")

    # 统计数据
    print("\n数据统计:")
    cursor.execute("SELECT COUNT(*) FROM chat_messages")
    print(f"  chat_messages: {cursor.fetchone()[0]} 条")

    cursor.execute("SELECT COUNT(*) FROM group_chats")
    print(f"  group_chats: {cursor.fetchone()[0]} 个")

    cursor.execute("SELECT COUNT(*) FROM group_chat_members")
    print(f"  group_chat_members: {cursor.fetchone()[0]} 条关联")


def main():
    """主迁移函数"""
    print("=" * 60)
    print("聊天系统数据库迁移")
    print("=" * 60)

    # 备份数据库
    backup_database()

    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        # 检查现有表
        check_existing_tables(conn)

        # 执行迁移
        migrate_chat_messages(conn)
        create_group_chat_members_table(conn)
        migrate_group_chat_members(conn)
        update_group_chats_table(conn)

        # 验证
        verify_migration(conn)

        # 提交更改
        conn.commit()
        print("\n" + "=" * 60)
        print("✓ 迁移成功完成！")
        print("=" * 60)
        print(f"\n数据库已更新，备份文件位于: {BACKUP_PATH}")

    except Exception as e:
        conn.rollback()
        print("\n" + "=" * 60)
        print("✗ 迁移失败！")
        print("=" * 60)
        print(f"\n错误: {e}")
        print(f"\n数据库已回滚，可以使用备份文件恢复: {BACKUP_PATH}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
