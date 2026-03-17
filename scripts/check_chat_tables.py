"""
检查聊天系统表结构
"""
import sqlite3

DB_PATH = "D:/SocialClaw/data/sqlite/socialclaw.db"

conn = sqlite3.connect(DB_PATH)

print("=== chat_messages 表结构 ===")
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(chat_messages)")
columns = cursor.fetchall()
for col in columns:
    print(f"{col[1]:25} {col[2]:15} {'NOT NULL' if col[3] else 'NULLABLE':10}")

print("\n=== group_chats 表结构 ===")
cursor.execute("PRAGMA table_info(group_chats)")
columns = cursor.fetchall()
for col in columns:
    print(f"{col[1]:25} {col[2]:15} {'NOT NULL' if col[3] else 'NULLABLE':10}")

print("\n=== 检查 group_chat_members 表 ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='group_chat_members'")
if cursor.fetchone():
    print("group_chat_members 表存在")
    cursor.execute("PRAGMA table_info(group_chat_members)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"{col[1]:25} {col[2]:15} {'NOT NULL' if col[3] else 'NULLABLE':10}")
else:
    print("group_chat_members 表不存在")

conn.close()
