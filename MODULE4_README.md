# SocialClaw 模块四：聊天系统

> **模块状态**: ✅ 已生成完整代码

## 模块概述

模块四提供一对一聊天、群聊、消息历史记录等功能，是 SocialClaw 项目的核心通信模块。

## 技术栈

- **FastAPI 0.115.0** - Web 框架
- **SQLAlchemy 2.0** - ORM
- **Pydantic 2.8** - 数据验证
- **OAuth2 (Second Me)** - 认证

## 文件结构

```
socialclaw/
├── app/
│   ├── __init__.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── chat_service.py          # 聊天业务逻辑
│   └── api/
│       ├── __init__.py
│       └── v1/
│           ├── __init__.py
│           └── chat.py              # 聊天 API 路由
├── tests/
│   ├── __init__.py
│   └── test_chat.py                 # 测试文件
└── MODULE4_README.md                  # 本文件
```

## 功能特性

### 1. 一对一聊天
- 发送和接收消息
- 获取聊天历史
- 标记消息已读
- 删除消息

### 2. 群聊功能
- 创建群聊
- 群聊消息发送
- 获取群聊历史
- 获取用户加入的群列表

### 3. 消息管理
- 未读消息统计
- 消息分页查询
- 消息时间筛选
- 软删除（不物理删除）

## API 端点

### 发送消息
```
POST /api/v1/chat/messages
```

**请求体:**
```json
{
  "receiver_id": "soc_user_123",
  "content": "你好！"
}
```

或群聊:
```json
{
  "group_id": "group_abc123",
  "content": "大家好！"
}
```

### 获取聊天历史
```
GET /api/v1/chat/history?with_user_id=soc_user_123&skip=0&limit=50
```

或群聊历史:
```
GET /api/v1/chat/history?group_id=group_abc123
```

### 标记消息已读
```
POST /api/v1/chat/messages/{message_id}/read
```

### 获取未读数量
```
GET /api/v1/chat/unread/count
```

### 删除消息
```
DELETE /api/v1/chat/messages/{message_id}
```

### 创建群聊
```
POST /api/v1/chat/groups
```

**请求体:**
```json
{
  "name": "技术讨论群",
  "member_ids": ["user_1", "user_2", "user_3"]
}
```

### 获取群聊列表
```
GET /api/v1/chat/groups
```

## 数据依赖

### 数据库表
- `chat_messages` - 聊天消息表
- `group_chats` - 群聊表
- `group_chat_members` - 群聊成员表
- `connected_agents` - 关联用户表

### 数据模型存根
如果项目还没有完整的模型，代码中包含了简单的存根供测试使用。

## 服务层函数

### `send_message()`
发送消息（一对一或群聊）

### `get_chat_history()`
获取两个用户之间的聊天历史

### `mark_as_read()`
标记消息为已读

### `get_unread_count()`
获取未读消息数量

### `delete_message()`
删除消息（软删除）

### `create_group_chat()`
创建群聊

### `get_group_chat_messages()`
获取群聊消息历史

### `get_user_groups()`
获取用户加入的群聊列表

## 测试

运行测试:
```bash
pytest tests/test_chat.py -v
```

测试覆盖:
- ✅ 服务层单元测试
- ✅ API 端点 Schema 验证
- ✅ 集成测试（完整聊天流程）

## 集成到主应用

在 `app/main.py` 中添加:

```python
from app.api.v1.chat import router as chat_router

app.include_router(chat_router)
```

## 开发注意事项

1. **消息验证**: 内容长度限制 1-5000 字符
2. **权限控制**: 只有接收者可标记已读，只有发送者可删除
3. **软删除**: 使用 `is_deleted` 字段，不物理删除
4. **分页**: 默认 50 条，最大 100 条
5. **群聊**: 创建者自动加入，无需在 member_ids 中包含自己

## 与其他模块的关系

- 依赖模块一（认证）的 `get_current_user`
- 不直接依赖其他模块
- 通过数据库表解耦

---

**模块四开发完成！** 🎉

**存放路径**: `C:\Users\PC\socialclaw\`
