"""
聊天系统数据库迁移脚本（简化版）
创建 group_chat_members 表并迁移数据
"""
import sqlite3
import json
import shutil
from datetime import datetime


DB_PATH = "D:/SocialClaw/data/sqlite/socialclaw.db"
BACKUP_PATH = "D:/SocialClaw/data/sqlite/socialclaw_backup_{}.db".format(
    datetime.now().strftime("%Y%m%d_%H%M%S")
)


def backup_database():
    """备份数据库"""
    print(f"[INFO] 正在备份数据库到: {BACKUP_PATH}")
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print("[OK] 备份完成")


def create_group_chat_members_table(conn):
    """创建 group_chat_members 关联表"""
    cursor = conn.cursor()

    # 检查表是否已存在
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='group_chat_members'
    """)

    if cursor.fetchone():
        print("[INFO] group_chat_members 表已存在，跳过创建")
        return

    print("[INFO] 创建 group_chat_members 表...")

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

    print("[OK] group_chat_members 表创建完成")


def migrate_group_chat_members(conn):
    """迁移现有群聊的成员数据"""
    cursor = conn.cursor()

    print("\n[INFO] 检查是否需要迁移群聊成员数据...")

    # 检查 group_chats 表是否有 members 列
    cursor.execute("PRAGMA table_info(group_chats)")
    columns = {col[1]: col for col in cursor.fetchall()}

    if 'members' not in columns:
        print("  [INFO] group_chats 表没有 members 列，无需迁移")
        return

    print("  [INFO] 发现 members 列，开始迁移数据...")

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
            print(f"  [WARN] 跳过无效的 JSON: group_id={group_id}")
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

    print(f"[OK] 已迁移 {migrated_count} 条群聊成员记录")


def update_group_chats_table(conn):
    """更新 group_chats 表 - 移除 members 列，添加 is_deleted 和 updated_at"""
    cursor = conn.cursor()

    print("\n[INFO] 更新 group_chats 表结构...")

    # 检查是否需要更新
    cursor.execute("PRAGMA table_info(group_chats)")
    columns = {col[1]: col for col in cursor.fetchall()}

    if 'members' not in columns and 'is_deleted' in columns:
        print("  [INFO] group_chats 表结构已是最新，无需更新")
        return

    # 重建表
    print("  [INFO] 重建 group_chats 表...")

    # 1. 添加 is_deleted 和 updated_at 列（如果不存在）
    if 'is_deleted' not in columns:
        print("    添加 is_deleted 列...")
        cursor.execute("ALTER TABLE group_chats ADD COLUMN is_deleted BOOLEAN DEFAULT 0")

    if 'updated_at' not in columns:
        print("    添加 updated_at 列...")
        cursor.execute("ALTER TABLE group_chats ADD COLUMN updated_at DATETIME")

        # 设置默认值
        cursor.execute("UPDATE group_chats SET updated_at = created_at WHERE updated_at IS NULL")

    # 2. 如果需要移除 members 列，重建表
    if 'members' in columns:
        print("    移除 members 列...")

        # 重命名旧表
        cursor.execute("ALTER TABLE group_chats RENAME TO group_chats_old")

        # 创建新表
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

        # 复制数据（排除 members 列）
        cursor.execute("""
            INSERT INTO group_chats
            (group_id, name, description, creator_agent_id, is_public, is_deleted, created_at, updated_at)
            SELECT group_id, name, description, creator_agent_id, is_public, is_deleted, created_at, updated_at
            FROM group_chats_old
        """)

        # 重建索引（如果不存在）
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='ix_group_chats_group_id'
        """)
        if not cursor.fetchone():
            cursor.execute("CREATE INDEX ix_group_chats_group_id ON group_chats (group_id)")

        # 删除旧表
        cursor.execute("DROP TABLE group_chats_old")

    print("[OK] group_chats 表更新完成")


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
        # 执行迁移
        create_group_chat_members_table(conn)
        migrate_group_chat_members(conn)
        update_group_chats_table(conn)

        # 验证
        verify_migration(conn)

        # 提交更改
        conn.commit()
        print("\n" + "=" * 60)
        print("[OK] 迁移成功完成！")
        print("=" * 60)
        print(f"\n数据库已更新，备份文件位于: {BACKUP_PATH}")

    except Exception as e:
        conn.rollback()
        print("\n" + "=" * 60)
        print("[ERROR] 迁移失败！")
        print("=" * 60)
        print(f"\n错误: {e}")
        print(f"\n数据库已回滚，可以使用备份文件恢复: {BACKUP_PATH}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
