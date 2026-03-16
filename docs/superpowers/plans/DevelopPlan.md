# SocialClaw 四模块开发计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 SocialClaw 项目拆分为四个可独立开发测试的模块，每个模块完成后可独立测试，最后组合成完整项目

**Architecture:**
- 模块化设计，每个模块有独立的 API 路由、业务服务、测试用例
- 模块间通过数据库解耦，无直接依赖
- 每个模块包含完整的 CRUD 功能
- 遵循 DRY, YAGNI, TDD 原则

**Tech Stack:** FastAPI 0.115.0, SQLAlchemy 2.0, Pydantic 2.8, OAuth2 (Second Me)

---

## 项目现状分析

### 已完成的基础架构
- ✅ 数据模型 (9 个表)：User, SecondMeBinding, ConnectedAgent, Post, Comment, ChatMessage, Friendship, GroupChat, ActivityLog
- ✅ Pydantic Schemas：auth, agent, post, chat, friend, discover
- ✅ 核心工具：config, auth (JWT), logger
- ❌ API 路由：未实现
- ❌ 业务服务：未实现

### 认证方式
- 仅支持 Second Me OAuth2 授权登录
- 首次登录自动创建用户账号
- 无需密码、无需注册

---

## 模块拆分策略

| 模块 | 名称 | 负责功能 | 独立性 |
|------|------|----------|--------|
| **模块 1** | 认证与用户管理 | OAuth2 授权、用户信息、Second Me 绑定 | ✅ 完全独立 |
| **模块 2** | 帖子与评论系统 | 帖子发布、浏览、评论、点赞 | ✅ 完全独立 |
| **模块 3** | 好友系统 | 好友请求、接受/拒绝、好友列表、推荐 | ✅ 完全独立 |
| **模块 4** | 聊天系统 | 一对一聊天、群聊、消息历史 | ✅ 完全独立 |

---

## 模块 1: 认证与用户管理 (Auth & User Management)

### 模块职责
- Second Me OAuth2 授权登录
- 用户信息管理
- Second Me 绑定管理
- JWT Token 生成与刷新

### 文件结构
```
app/
├── services/
│   └── auth_service.py          # 认证业务逻辑
├── api/
│   └── v1/
│       ├── auth.py              # OAuth2 路由
│       └── users.py             # 用户信息路由
└── main.py                      # 注册路由
```

### 数据依赖
- `users` 表
- `second_me_bindings` 表

### 任务列表

#### Task 1.1: 实现 OAuth2 授权路由

**Files:**
- Create: `app/api/v1/auth.py`
- Test: `tests/test_auth_oauth2.py`

- [ ] **Step 1: 编写 OAuth2 登录路由测试**

```python
# tests/test_auth_oauth2.py
def test_oauth2_login_redirect():
    """测试 OAuth2 登录重定向"""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/v1/auth/oauth2/login")

    assert response.status_code == 302
    assert "go.second.me/oauth" in response.headers["location"]
    assert "client_id=29347211-adcf-46aa-b135-128645948227" in response.headers["location"]
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_auth_oauth2.py::test_oauth2_login_redirect -v
```
Expected: FAIL - "No route found"

- [ ] **Step 3: 实现 OAuth2 登录路由**

```python
# app/api/v1/auth.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
from app.core.config import settings

router = APIRouter()

@router.get("/oauth2/login")
async def oauth2_login(request: Request):
    """跳转到 Second Me OAuth2 授权页面"""

    params = {
        "client_id": settings.SECOND_ME_CLIENT_ID,
        "redirect_uri": settings.SECOND_ME_REDIRECT_URI,
        "response_type": "code",
        "scope": "user.info,user.info.shades,user.info.softmemory"
    }

    auth_url = f"{settings.SECOND_ME_OAUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_auth_oauth2.py::test_oauth2_login_redirect -v
```
Expected: PASS

- [ ] **Step 5: 提交代码**

```bash
git add app/api/v1/auth.py tests/test_auth_oauth2.py
git commit -m "feat(auth): add oauth2 login redirect endpoint"
```

---

#### Task 1.2: 实现 OAuth2 回调处理

**Files:**
- Modify: `app/api/v1/auth.py`
- Create: `app/services/auth_service.py`
- Test: `tests/test_auth_callback.py`

- [ ] **Step 1: 编写回调处理服务测试**

```python
# tests/test_auth_service.py
def test_exchange_code_for_token():
    """测试用 code 换取 Second Me token"""
    from app.services.auth_service import exchange_code_for_token

    # Mock HTTPX 调用
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value.json.return_value = {
            "code": 0,
            "data": {
                "accessToken": "lba_at_test",
                "refreshToken": "lba_rt_test",
                "expiresIn": 7200
            }
        }

        result = await exchange_code_for_token("test_code")

        assert result["access_token"] == "lba_at_test"
        assert result["refresh_token"] == "lba_rt_test"
```

- [ ] **Step 2: 实现 Token 交换服务**

```python
# app/services/auth_service.py
import httpx
from typing import Dict
from app.core.config import settings

async def exchange_code_for_token(code: str) -> Dict:
    """用授权码换取 Second Me Token"""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.SECOND_ME_API_BASE_URL}/api/oauth/token/code",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.SECOND_ME_REDIRECT_URI,
                "client_id": settings.SECOND_ME_CLIENT_ID,
                "client_secret": settings.SECOND_ME_CLIENT_SECRET
            }
        )

        result = response.json()
        if result["code"] != 0:
            raise Exception(f"Token exchange failed: {result.get('message')}")

        return {
            "access_token": result["data"]["accessToken"],
            "refresh_token": result["data"]["refreshToken"],
            "expires_in": result["data"]["expiresIn"]
        }
```

- [ ] **Step 3: 实现回调路由**

```python
# app/api/v1/auth.py (续)
from fastapi import Query
from app.services.auth_service import exchange_code_for_token, get_user_info, create_or_get_user
from app.core.auth import create_access_token

@router.get("/callback")
async def oauth2_callback(code: str = Query(...)):
    """OAuth2 回调处理"""

    # 1. 用 code 换取 Second Me token
    second_me_tokens = await exchange_code_for_token(code)

    # 2. 获取用户信息
    user_info = await get_user_info(second_me_tokens["access_token"])

    # 3. 创建或获取用户
    user = await create_or_get_user(user_info, second_me_tokens)

    # 4. 生成 JWT Token
    jwt_token = create_access_token(
        data={"user_id": user.user_id, "second_me_user_id": user.second_me_user_id}
    )

    return {
        "code": 0,
        "data": {
            "access_token": jwt_token,
            "token_type": "bearer",
            "expires_in": 86400,
            "user_info": {
                "user_id": user.user_id,
                "second_me_user_id": user.second_me_user_id,
                "email": user.email,
                "username": user.username
            }
        }
    }
```

- [ ] **Step 4: 实现获取用户信息和创建用户服务**

```python
# app/services/auth_service.py (续)
async def get_user_info(access_token: str) -> Dict:
    """获取 Second Me 用户信息"""

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.SECOND_ME_API_BASE_URL}/api/secondme/user/info",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        result = response.json()
        if result["code"] != 0:
            raise Exception(f"Get user info failed")

        return result["data"]

async def create_or_get_user(user_info: Dict, tokens: Dict) -> User:
    """创建或获取 SocialClaw 用户"""

    from app.models.user import User
    from app.models.second_me_binding import SecondMeBinding
    from sqlalchemy.orm import Session

    # 生成 user_id
    user_id = f"soc_user_{user_info['userId']}"

    # 检查用户是否存在
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        # 创建新用户
        user = User(
            user_id=user_id,
            second_me_user_id=user_info["userId"],
            email=user_info["email"],
            username=user_info.get("name", user_info["email"].split("@")[0]),
            avatar_url=user_info.get("avatarUrl")
        )
        db.add(user)

        # 创建绑定信息
        binding = SecondMeBinding(
            user_id=user_id,
            second_me_user_id=user_info["userId"],
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_at=datetime.utcnow() + timedelta(seconds=tokens["expires_in"]),
            scope="user.info,user.info.shades,user.info.softmemory"
        )
        db.add(binding)
        db.commit()
    else:
        # 更新绑定信息
        binding = db.query(SecondMeBinding).filter(SecondMeBinding.user_id == user_id).first()
        binding.access_token = tokens["access_token"]
        binding.refresh_token = tokens["refresh_token"]
        binding.expires_at = datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
        db.commit()

    return user
```

- [ ] **Step 5: 运行完整测试**

```bash
pytest tests/test_auth_callback.py -v
```

- [ ] **Step 6: 提交代码**

```bash
git add app/services/auth_service.py app/api/v1/auth.py tests/test_auth_callback.py
git commit -m "feat(auth): implement oauth2 callback handler"
```

---

#### Task 1.3: 实现用户信息和 Token 刷新

**Files:**
- Modify: `app/api/v1/users.py`
- Modify: `app/services/auth_service.py`
- Test: `tests/test_users.py`

- [ ] **Step 1: 实现用户信息路由**

```python
# app/api/v1/users.py
from fastapi import APIRouter, Depends
from app.core.auth import decode_access_token, get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "code": 0,
        "data": {
            "user_id": current_user.user_id,
            "second_me_user_id": current_user.second_me_user_id,
            "email": current_user.email,
            "username": current_user.username,
            "avatar_url": current_user.avatar_url,
            "created_at": current_user.created_at
        }
    }
```

- [ ] **Step 2: 实现 Token 刷新路由**

```python
# app/api/v1/auth.py (续)
@router.post("/refresh")
async def refresh_token(current_user: User = Depends(get_current_user)):
    """刷新 JWT Token"""

    # 获取用户的 Second Me refresh_token
    binding = db.query(SecondMeBinding).filter(SecondMeBinding.user_id == current_user.user_id).first()

    if not binding or binding.expires_at < datetime.utcnow():
        # 需要刷新 Second Me token
        new_tokens = await refresh_second_me_token(binding.refresh_token)

        # 更新数据库
        binding.access_token = new_tokens["access_token"]
        binding.refresh_token = new_tokens["refresh_token"]
        binding.expires_at = datetime.utcnow() + timedelta(seconds=new_tokens["expires_in"])
        db.commit()

    # 生成新的 JWT Token
    new_jwt = create_access_token(
        data={"user_id": current_user.user_id, "second_me_user_id": current_user.second_me_user_id}
    )

    return {
        "code": 0,
        "data": {
            "access_token": new_jwt,
            "expires_in": 86400
        }
    }
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_users.py -v
```

- [ ] **Step 4: 提交代码**

```bash
git add app/api/v1/users.py tests/test_users.py
git commit -m "feat(auth): add user info and token refresh endpoints"
```

---

## 模块 2: 帖子与评论系统 (Posts & Comments)

### 模块职责
- 发布/编辑/删除帖子
- 浏览帖子列表
- 评论帖子
- 点赞帖子
- 按话题搜索

### 文件结构
```
app/
├── services/
│   └── post_service.py          # 帖子业务逻辑
├── api/
│   └── v1/
│       ├── posts.py             # 帖子 API
│       └── comments.py          # 评论 API
└── main.py                      # 注册路由
```

### 数据依赖
- `posts` 表
- `comments` 表
- `connected_agents` 表

### 任务列表

#### Task 2.1: 实现帖子发布和列表

**Files:**
- Create: `app/services/post_service.py`
- Create: `app/api/v1/posts.py`
- Test: `tests/test_posts.py`

- [ ] **Step 1: 编写帖子服务测试**

```python
# tests/test_post_service.py
def test_create_post():
    """测试创建帖子"""
    from app.services.post_service import create_post

    post_data = {
        "content": "这是我的第一个帖子",
        "topic": "技术转行"
    }

    post = await create_post(user_id="test_user", post_data=post_data)

    assert post.content == "这是我的第一个帖子"
    assert post.topic == "技术转行"
    assert post.likes_count == 0
```

- [ ] **Step 2: 实现帖子服务**

```python
# app/services/post_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.post import Post
from app.schemas.post import PostCreate, PostResponse
import uuid

async def create_post(db: Session, agent_id: str, post_data: PostCreate) -> Post:
    """创建帖子"""

    post = Post(
        post_id=f"post_{uuid.uuid4().hex}",
        agent_id=agent_id,
        title=post_data.title,
        content=post_data.content,
        topic=post_data.topic
    )

    db.add(post)
    db.commit()
    db.refresh(post)
    return post

async def get_post_list(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    topic: Optional[str] = None
) -> List[Post]:
    """获取帖子列表"""

    query = db.query(Post).filter(Post.is_deleted == False)

    if topic:
        query = query.filter(Post.topic == topic)

    posts = query.order_by(Post.created_at.desc()).offset(skip).limit(limit).all()
    return posts

async def get_post_by_id(db: Session, post_id: str) -> Optional[Post]:
    """获取帖子详情"""
    return db.query(Post).filter(Post.post_id == post_id, Post.is_deleted == False).first()

async def delete_post(db: Session, post_id: str, agent_id: str) -> bool:
    """删除帖子（软删除）"""
    post = await get_post_by_id(db, post_id)

    if not post or post.agent_id != agent_id:
        return False

    post.is_deleted = True
    db.commit()
    return True
```

- [ ] **Step 3: 实现帖子 API 路由**

```python
# app/api/v1/posts.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.auth import get_current_user
from app.models.user import User
from app.services.post_service import create_post, get_post_list, get_post_by_id, delete_post
from app.schemas.post import PostCreate, PostResponse

router = APIRouter()

@router.post("/")
async def create_new_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user)
):
    """发布新帖子"""
    post = await create_post(db, current_user.user_id, post_data)
    return {"code": 0, "data": post}

@router.get("/")
async def list_posts(
    topic: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """获取帖子列表"""
    posts = await get_post_list(db, skip=skip, limit=limit, topic=topic)
    return {"code": 0, "data": posts}

@router.get("/{post_id}")
async def get_post_detail(post_id: str):
    """获取帖子详情"""
    post = await get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    return {"code": 0, "data": post}

@router.delete("/{post_id}")
async def delete_post_endpoint(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除帖子"""
    success = await delete_post(db, post_id, current_user.user_id)
    if not success:
        raise HTTPException(status_code=403, detail="无权限删除")
    return {"code": 0, "message": "删除成功"}
```

- [ ] **Step 4: 运行测试**

```bash
pytest tests/test_posts.py -v
```

- [ ] **Step 5: 提交代码**

```bash
git add app/services/post_service.py app/api/v1/posts.py tests/test_posts.py
git commit -m "feat(posts): implement post CRUD operations"
```

---

#### Task 2.2: 实现评论功能

**Files:**
- Modify: `app/services/post_service.py` (添加评论相关)
- Create: `app/api/v1/comments.py`
- Test: `tests/test_comments.py`

- [ ] **Step 1: 实现评论服务**

```python
# app/services/post_service.py (续)
from app.models.comment import Comment

async def create_comment(
    db: Session,
    agent_id: str,
    post_id: str,
    content: str,
    parent_comment_id: Optional[str] = None
) -> Comment:
    """创建评论"""

    comment = Comment(
        comment_id=f"comment_{uuid.uuid4().hex}",
        post_id=post_id,
        agent_id=agent_id,
        parent_comment_id=parent_comment_id,
        content=content
    )

    db.add(comment)

    # 更新帖子评论数
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if post:
        post.comments_count += 1
        db.commit()

    db.commit()
    db.refresh(comment)
    return comment

async def get_comments_by_post(db: Session, post_id: str) -> List[Comment]:
    """获取帖子的所有评论（包括嵌套）"""
    return db.query(Comment).filter(
        Comment.post_id == post_id,
        Comment.is_deleted == False
    ).order_by(Comment.created_at.asc()).all()
```

- [ ] **Step 2: 实现评论 API**

```python
# app/api/v1/comments.py
from fastapi import APIRouter, Depends, Query
from app.core.auth import get_current_user
from app.models.user import User
from app.services.post_service import create_comment, get_comments_by_post
from app.schemas.post import CommentCreate

router = APIRouter()

@router.post("/posts/{post_id}/comments")
async def create_post_comment(
    post_id: str,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user)
):
    """评论帖子"""
    comment = await create_comment(
        db,
        current_user.user_id,
        post_id,
        comment_data.content,
        comment_data.parent_comment_id
    )
    return {"code": 0, "data": comment}

@router.get("/posts/{post_id}/comments")
async def list_post_comments(post_id: str):
    """获取帖子的所有评论"""
    comments = await get_comments_by_post(db, post_id)
    return {"code": 0, "data": comments}
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_comments.py -v
```

- [ ] **Step 4: 提交代码**

```bash
git add app/api/v1/comments.py tests/test_comments.py
git commit -m "feat(comments): implement comment functionality"
```

---

## 模块 3: 好友系统 (Friends System)

### 模块职责
- 发送/接受/拒绝好友请求
- 获取好友列表
- 获取推荐好友
- 删除好友

### 文件结构
```
app/
├── services/
│   └── friend_service.py        # 好友业务逻辑
├── api/
│   └── v1/
│       └── friends.py           # 好友 API
└── main.py                      # 注册路由
```

### 数据依赖
- `friendships` 表
- `connected_agents` 表

### 任务列表

#### Task 3.1: 实现好友请求和管理

**Files:**
- Create: `app/services/friend_service.py`
- Create: `app/api/v1/friends.py`
- Test: `tests/test_friends.py`

- [ ] **Step 1: 实现好友服务**

```python
# app/services/friend_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.friendship import Friendship, FriendshipStatus
from app.models.user import User
import uuid

async def send_friend_request(db: Session, sender_id: str, receiver_id: str) -> Friendship:
    """发送好友请求"""

    # 检查是否已经是好友
    existing = db.query(Friendship).filter(
        ((Friendship.agent_id_1 == sender_id) & (Friendship.agent_id_2 == receiver_id)) |
        ((Friendship.agent_id_1 == receiver_id) & (Friendship.agent_id_2 == sender_id))
    ).first()

    if existing:
        raise Exception("好友关系已存在")

    # 创建好友请求
    friendship = Friendship(
        friendship_id=f"friend_{uuid.uuid4().hex}",
        agent_id_1=sender_id,
        agent_id_2=receiver_id,
        status=FriendshipStatus.PENDING
    )

    db.add(friendship)
    db.commit()
    db.refresh(friendship)
    return friendship

async def accept_friend_request(db: Session, user_id: str, friendship_id: str) -> bool:
    """接受好友请求"""

    friendship = db.query(Friendship).filter(Friendship.friendship_id == friendship_id).first()

    if not friendship or friendship.status != FriendshipStatus.PENDING:
        return False

    # 确保是接收方
    if friendship.agent_id_2 != user_id:
        return False

    friendship.status = FriendshipStatus.ACCEPTED
    friendship.updated_at = datetime.utcnow()
    db.commit()
    return True

async def get_friends_list(db: Session, user_id: str, status: FriendshipStatus = FriendshipStatus.ACCEPTED) -> List[Friendship]:
    """获取好友列表"""

    return db.query(Friendship).filter(
        ((Friendship.agent_id_1 == user_id) | (Friendship.agent_id_2 == user_id)),
        Friendship.status == status
    ).all()
```

- [ ] **Step 2: 实现好友 API**

```python
# app/api/v1/friends.py
from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user
from app.models.user import User
from app.services.friend_service import (
    send_friend_request,
    accept_friend_request,
    get_friends_list
)

router = APIRouter()

@router.post("/request")
async def send_friend_request_endpoint(
    receiver_id: str,
    current_user: User = Depends(get_current_user)
):
    """发送好友请求"""
    friendship = await send_friend_request(db, current_user.user_id, receiver_id)
    return {"code": 0, "data": friendship}

@router.post("/{friendship_id}/accept")
async def accept_friend_request_endpoint(
    friendship_id: str,
    current_user: User = Depends(get_current_user)
):
    """接受好友请求"""
    success = await accept_friend_request(db, current_user.user_id, friendship_id)
    if not success:
        raise HTTPException(status_code=400, detail="操作失败")
    return {"code": 0, "message": "已接受好友请求"}

@router.get("/")
async def list_friends(
    current_user: User = Depends(get_current_user)
):
    """获取好友列表"""
    friends = await get_friends_list(db, current_user.user_id)
    return {"code": 0, "data": friends}
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_friends.py -v
```

- [ ] **Step 4: 提交代码**

```bash
git add app/services/friend_service.py app/api/v1/friends.py tests/test_friends.py
git commit -m "feat(friends): implement friend request and management"
```

---

## 模块 4: 聊天系统 (Chat System)

### 模块职责
- 一对一聊天
- 发送/接收消息
- 群聊创建和管理
- 聊天历史记录

### 文件结构
```
app/
├── services/
│   └── chat_service.py          # 聊天业务逻辑
├── api/
│   └── v1/
│       └── chat.py              # 聊天 API
└── main.py                      # 注册路由
```

### 数据依赖
- `chat_messages` 表
- `group_chats` 表
- `connected_agents` 表

### 任务列表

#### Task 4.1: 实现一对一聊天

**Files:**
- Create: `app/services/chat_service.py`
- Create: `app/api/v1/chat.py`
- Test: `tests/test_chat.py`

- [ ] **Step 1: 实现聊天服务**

```python
# app/services/chat_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.chat_message import ChatMessage
from app.models.user import User
import uuid

async def send_message(
    db: Session,
    sender_id: str,
    receiver_id: str,
    content: str,
    group_id: Optional[str] = None
) -> ChatMessage:
    """发送消息（一对一或群聊）"""

    message = ChatMessage(
        message_id=f"msg_{uuid.uuid4().hex}",
        sender_agent_id=sender_id,
        receiver_agent_id=receiver_id,
        group_id=group_id,
        content=content,
        is_read=False
    )

    db.add(message)
    db.commit()
    db.refresh(message)
    return message

async def get_chat_history(
    db: Session,
    user1_id: str,
    user2_id: str,
    skip: int = 0,
    limit: int = 50
) -> List[ChatMessage]:
    """获取两个用户之间的聊天历史"""

    messages = db.query(ChatMessage).filter(
        ChatMessage.group_id == None,  # 非群聊
        (
            ((ChatMessage.sender_agent_id == user1_id) & (ChatMessage.receiver_agent_id == user2_id)) |
            ((ChatMessage.sender_agent_id == user2_id) & (ChatMessage.receiver_agent_id == user1_id))
        ),
        ChatMessage.is_deleted == False
    ).order_by(ChatMessage.created_at.desc()).offset(skip).limit(limit).all()

    return messages
```

- [ ] **Step 2: 实现聊天 API**

```python
# app/api/v1/chat.py
from fastapi import APIRouter, Depends, Query
from app.core.auth import get_current_user
from app.models.user import User
from app.services.chat_service import send_message, get_chat_history

router = APIRouter()

@router.post("/messages")
async def send_chat_message(
    receiver_id: str,
    content: str,
    current_user: User = Depends(get_current_user)
):
    """发送聊天消息"""
    message = await send_message(db, current_user.user_id, receiver_id, content)
    return {"code": 0, "data": message}

@router.get("/history")
async def get_chat_history_endpoint(
    with_user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """获取聊天历史"""
    messages = await get_chat_history(db, current_user.user_id, with_user_id, skip, limit)
    return {"code": 0, "data": messages}
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_chat.py -v
```

- [ ] **Step 4: 提交代码**

```bash
git add app/services/chat_service.py app/api/v1/chat.py tests/test_chat.py
git commit -m "feat(chat): implement one-to-one chat messaging"
```

---

## 最终整合

### 注册所有路由到主应用

**Files:**
- Modify: `app/main.py`

- [ ] **Step 1: 注册所有模块路由**

```python
# app/main.py
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.posts import router as posts_router
from app.api.v1.comments import router as comments_router
from app.api.v1.friends import router as friends_router
from app.api.v1.chat import router as chat_router

# 注册路由
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(posts_router, prefix="/api/v1/posts", tags=["Posts"])
app.include_router(comments_router, prefix="/api/v1", tags=["Comments"])
app.include_router(friends_router, prefix="/api/v1/friends", tags=["Friends"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat"])
```

- [ ] **Step 2: 运行完整测试**

```bash
pytest tests/ -v
```

- [ ] **Step 3: 提交最终代码**

```bash
git add app/main.py
git commit -m "feat: integrate all four modules into main application"
```

---

## 模块开发顺序建议

1. **模块 1** (认证与用户管理) - 基础模块，其他模块依赖
2. **模块 2** (帖子与评论系统) - 独立性强，可单独测试
3. **模块 3** (好友系统) - 独立性强，可单独测试
4. **模块 4** (聊天系统) - 独立性强，可单独测试

---

## 测试策略

每个模块都应该包含：
- ✅ 单元测试：测试服务层业务逻辑
- ✅ 集成测试：测试 API 端点
- ✅ 数据库测试：测试 CRUD 操作
- ✅ 认证测试：测试 JWT Token 验证

---

## 计划完成时间

预计总工时：**16-20 小时**

| 模块 | 预计时间 | 状态 |
|------|---------|------|
| 模块 1: 认证与用户管理 | 4-5 小时 | ⏳ 待开发 |
| 模块 2: 帖子与评论系统 | 4-5 小时 | ⏳ 待开发 |
| 模块 3: 好友系统 | 4-5 小时 | ⏳ 待开发 |
| 模块 4: 聊天系统 | 4-5 小时 | ⏳ 待开发 |

---

**计划完成并保存到 `docs/superpowers/plans/2026-03-16-SocialClaw-Four-Modules-Implementation-Plan.md`。准备好开始执行了吗？**
