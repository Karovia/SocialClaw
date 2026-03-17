# 模块 2：帖子与评论系统实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现完整的帖子发布、浏览、编辑、删除功能，以及评论系统（包括嵌套回复）和点赞功能。

**Architecture:**
- 服务层 (`post_service.py`) 封装所有业务逻辑，包括帖子 CRUD、评论管理、点赞操作
- API 层 (`posts.py`, `comments.py`) 负责 HTTP 请求处理和响应格式化
- 测试层采用 TDD 方式，每个功能先写测试再实现
- 模块独立，通过数据库与认证模块解耦

**Tech Stack:** FastAPI 0.115.0, SQLAlchemy 2.0, Pydantic 2.8, pytest

**Data Dependencies:**
- `posts` 表 - 帖子数据
- `comments` 表 - 评论数据
- `connected_agents` 表 - 关联用户 Agent ID
- `likes` 表 - 点赞记录（如存在）

---

## 文件结构总览

```
app/
├── services/
│   └── post_service.py          # 帖子与评论业务逻辑
├── api/
│   └── v1/
│       ├── posts.py             # 帖子 API 路由
│       └── comments.py          # 评论 API 路由
├── schemas/
│   └── post.py                  # Pydantic  schemas（已存在）
├── models/
│   ├── post.py                  # Post 模型（已存在）
│   └── comment.py               # Comment 模型（已存在）
└── main.py                      # 注册路由
tests/
├── test_posts.py                # 帖子功能测试
├── test_comments.py             # 评论功能测试
└── test_post_likes.py           # 点赞功能测试
```

---

## Chunk 1: 帖子基础服务与发布功能

### Task 1.1: 实现帖子服务层 - 发布帖子

**Files:**
- Create: `app/services/post_service.py`
- Test: `tests/test_posts.py::test_create_post`

- [ ] **Step 1: 编写创建帖子测试**

```python
# tests/test_posts.py
import pytest
from sqlalchemy.orm import Session
from app.services.post_service import create_post
from app.schemas.post import PostCreate
from app.models.user import User

def test_create_post(db: Session, test_user: User):
    """测试创建帖子"""
    post_data = PostCreate(
        content="这是我的第一个帖子 #技术转行",
        topic="技术转行"
    )

    post = create_post(db, test_user.user_id, post_data)

    assert post.content == "这是我的第一个帖子 #技术转行"
    assert post.topic == "技术转行"
    assert post.likes_count == 0
    assert post.comments_count == 0
    assert post.is_deleted == False
    assert post.agent_id == test_user.user_id
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_posts.py::test_create_post -v
```
Expected: FAIL - "ModuleNotFoundError: No module named 'app.services.post_service'"

- [ ] **Step 3: 实现帖子服务层基础**

```python
# app/services/post_service.py
"""帖子与评论业务逻辑服务"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.post import Post
from app.schemas.post import PostCreate
import uuid
from datetime import datetime


def create_post(db: Session, agent_id: str, post_data: PostCreate) -> Post:
    """
    创建新帖子

    Args:
        db: 数据库会话
        agent_id: 用户/Agent ID
        post_data: 帖子创建数据

    Returns:
        创建的 Post 对象
    """
    post = Post(
        post_id=f"post_{uuid.uuid4().hex}",
        agent_id=agent_id,
        content=post_data.content,
        topic=post_data.topic,
        likes_count=0,
        comments_count=0,
        is_deleted=False
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    return post
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_posts.py::test_create_post -v
```
Expected: PASS

- [ ] **Step 5: 提交代码**

```bash
git add app/services/post_service.py tests/test_posts.py
git commit -m "feat(posts): add create_post service function with TDD"
```

---

### Task 1.2: 实现帖子服务层 - 获取帖子列表

**Files:**
- Modify: `app/services/post_service.py`
- Test: `tests/test_posts.py::test_get_post_list`

- [ ] **Step 1: 编写帖子列表测试**

```python
# tests/test_posts.py
def test_get_post_list(db: Session, test_user: User):
    """测试获取帖子列表"""
    # 创建测试数据
    post1 = create_post(db, test_user.user_id, PostCreate(content="帖子 1", topic="技术转行"))
    post2 = create_post(db, test_user.user_id, PostCreate(content="帖子 2", topic="职场"))
    post3 = create_post(db, test_user.user_id, PostCreate(content="帖子 3", topic="技术转行"))

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
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_posts.py::test_get_post_list -v
```
Expected: FAIL - "NameError: name 'get_post_list' is not defined"

- [ ] **Step 3: 实现帖子列表服务**

```python
# app/services/post_service.py (续)

def get_post_list(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    topic: Optional[str] = None
) -> List[Post]:
    """
    获取帖子列表（分页 + 话题过滤）

    Args:
        db: 数据库会话
        skip: 跳过记录数
        limit: 返回记录数上限
        topic: 可选的话题过滤

    Returns:
        Post 对象列表，按创建时间倒序
    """
    from sqlalchemy import desc

    query = db.query(Post).filter(
        Post.is_deleted == False
    )

    if topic:
        query = query.filter(Post.topic == topic)

    posts = query.order_by(desc(Post.created_at)).offset(skip).limit(limit).all()

    return posts
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_posts.py::test_get_post_list -v
```
Expected: PASS

- [ ] **Step 5: 提交代码**

```bash
git add app/services/post_service.py tests/test_posts.py
git commit -m "feat(posts): add get_post_list with pagination and topic filter"
```

---

### Task 1.3: 实现帖子服务层 - 获取帖子详情

**Files:**
- Modify: `app/services/post_service.py`
- Test: `tests/test_posts.py::test_get_post_by_id`

- [ ] **Step 1: 编写获取帖子详情测试**

```python
# tests/test_posts.py
def test_get_post_by_id(db: Session, test_user: User):
    """测试获取帖子详情"""
    post = create_post(db, test_user.user_id, PostCreate(content="测试帖子", topic="技术转行"))

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
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_posts.py::test_get_post_by_id -v
```
Expected: FAIL

- [ ] **Step 3: 实现获取帖子详情服务**

```python
# app/services/post_service.py (续)

def get_post_by_id(db: Session, post_id: str) -> Optional[Post]:
    """
    获取帖子详情

    Args:
        db: 数据库会话
        post_id: 帖子 ID

    Returns:
        Post 对象，不存在或已删除时返回 None
    """
    return db.query(Post).filter(
        Post.post_id == post_id,
        Post.is_deleted == False
    ).first()
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_posts.py::test_get_post_by_id -v
```
Expected: PASS

- [ ] **Step 5: 提交代码**

```bash
git add app/services/post_service.py tests/test_posts.py
git commit -m "feat(posts): add get_post_by_id with soft-delete check"
```

---

### Task 1.4: 实现帖子服务层 - 编辑帖子

**Files:**
- Modify: `app/services/post_service.py`
- Test: `tests/test_posts.py::test_update_post`

- [ ] **Step 1: 编写编辑帖子测试**

```python
# tests/test_posts.py
def test_update_post(db: Session, test_user: User):
    """测试编辑帖子"""
    post = create_post(db, test_user.user_id, PostCreate(content="原始内容", topic="技术转行"))

    # 测试正常更新
    updated = update_post(db, post.post_id, test_user.user_id, {
        "content": "更新后的内容",
        "topic": "职场"
    })

    assert updated is not None
    assert updated.content == "更新后的内容"
    assert updated.topic == "职场"

    # 测试更新不存在的帖子
    not_found = update_post(db, "post_nonexistent", test_user.user_id, {"content": "x"})
    assert not_found is None

    # 测试更新他人的帖子（权限检查）
    other_user = create_test_user(db)  # 假设有 helper 函数
    unauth = update_post(db, post.post_id, other_user.user_id, {"content": "x"})
    assert unauth is None  # 无权限返回 None
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_posts.py::test_update_post -v
```
Expected: FAIL

- [ ] **Step 3: 实现编辑帖子服务**

```python
# app/services/post_service.py (续)
from typing import Dict

def update_post(
    db: Session,
    post_id: str,
    agent_id: str,
    update_data: Dict[str, str]
) -> Optional[Post]:
    """
    编辑帖子（仅作者可编辑）

    Args:
        db: 数据库会话
        post_id: 帖子 ID
        agent_id: 用户/Agent ID（用于权限验证）
        update_data: 包含 content/topic 的字典

    Returns:
        更新后的 Post 对象，无权限或不存在时返回 None
    """
    post = get_post_by_id(db, post_id)

    if not post or post.agent_id != agent_id:
        return None

    # 只允许更新特定字段
    if "content" in update_data:
        post.content = update_data["content"]
    if "topic" in update_data:
        post.topic = update_data["topic"]

    db.commit()
    db.refresh(post)

    return post
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_posts.py::test_update_post -v
```
Expected: PASS

- [ ] **Step 5: 提交代码**

```bash
git add app/services/post_service.py tests/test_posts.py
git commit -m "feat(posts): add update_post with owner permission check"
```

---

### Task 1.5: 实现帖子服务层 - 删除帖子

**Files:**
- Modify: `app/services/post_service.py`
- Test: `tests/test_posts.py::test_delete_post`

- [ ] **Step 1: 编写删除帖子测试**

```python
# tests/test_posts.py
def test_delete_post(db: Session, test_user: User):
    """测试删除帖子（软删除）"""
    post = create_post(db, test_user.user_id, PostCreate(content="要删除的帖子", topic="技术转行"))

    # 测试正常删除
    result = delete_post(db, post.post_id, test_user.user_id)
    assert result == True

    # 验证软删除标志
    db.refresh(post)
    assert post.is_deleted == True

    # 验证删除后无法获取
    fetched = get_post_by_id(db, post.post_id)
    assert fetched is None

    # 测试删除不存在的帖子
    result2 = delete_post(db, "post_nonexistent", test_user.user_id)
    assert result2 == False

    # 测试删除他人的帖子
    post2 = create_post(db, test_user.user_id, PostCreate(content="帖子 2", topic="技术转行"))
    other_user = create_test_user(db)
    result3 = delete_post(db, post2.post_id, other_user.user_id)
    assert result3 == False
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_posts.py::test_delete_post -v
```
Expected: FAIL

- [ ] **Step 3: 实现删除帖子服务**

```python
# app/services/post_service.py (续)

def delete_post(db: Session, post_id: str, agent_id: str) -> bool:
    """
    删除帖子（软删除，仅作者可删除）

    Args:
        db: 数据库会话
        post_id: 帖子 ID
        agent_id: 用户/Agent ID（用于权限验证）

    Returns:
        删除成功返回 True，失败返回 False
    """
    post = get_post_by_id(db, post_id)

    if not post or post.agent_id != agent_id:
        return False

    post.is_deleted = True
    db.commit()

    return True
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_posts.py::test_delete_post -v
```
Expected: PASS

- [ ] **Step 5: 提交代码**

```bash
git add app/services/post_service.py tests/test_posts.py
git commit -m "feat(posts): add delete_post with soft-delete and permission check"
```

---

### Task 1.6: 实现帖子 API 路由

**Files:**
- Create: `app/api/v1/posts.py`
- Test: `tests/test_posts_api.py::test_create_post_api`

- [ ] **Step 1: 编写 API 测试**

```python
# tests/test_posts_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_post_api(auth_headers: dict):
    """测试创建帖子 API"""
    response = client.post(
        "/api/v1/posts/",
        headers=auth_headers,
        json={"content": "API 测试帖子", "topic": "测试"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["content"] == "API 测试帖子"
    assert data["data"]["topic"] == "测试"

def test_get_posts_api():
    """测试获取帖子列表 API"""
    response = client.get("/api/v1/posts/")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert isinstance(data["data"], list)

def test_get_post_detail_api(auth_headers: dict):
    """测试获取帖子详情 API"""
    # 先创建帖子
    create_resp = client.post("/api/v1/posts/", headers=auth_headers,
                               json={"content": "详情测试", "topic": "测试"})
    post_id = create_resp.json()["data"]["post_id"]

    # 获取详情
    response = client.get(f"/api/v1/posts/{post_id}")
    assert response.status_code == 200
    assert response.json()["data"]["content"] == "详情测试"

def test_delete_post_api(auth_headers: dict):
    """测试删除帖子 API"""
    create_resp = client.post("/api/v1/posts/", headers=auth_headers,
                               json={"content": "删除测试", "topic": "测试"})
    post_id = create_resp.json()["data"]["post_id"]

    # 删除
    response = client.delete(f"/api/v1/posts/{post_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["code"] == 0

    # 验证已删除
    get_resp = client.get(f"/api/v1/posts/{post_id}")
    assert get_resp.status_code == 404
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_posts_api.py -v
```
Expected: FAIL - 路由不存在

- [ ] **Step 3: 实现帖子 API 路由**

```python
# app/api/v1/posts.py
"""帖子 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.auth import get_current_user
from app.models.user import User
from app.services.post_service import (
    create_post, get_post_list, get_post_by_id, update_post, delete_post
)
from app.schemas.post import PostCreate, PostResponse
from app.database import get_db

router = APIRouter()


@router.post("/", response_model=PostResponse)
async def create_new_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发布新帖子"""
    post = create_post(db, current_user.user_id, post_data)
    return {"code": 0, "data": post}


@router.get("/", response_model=list[PostResponse])
async def list_posts(
    topic: Optional[str] = Query(None, description="话题过滤"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回上限"),
    db: Session = Depends(get_db)
):
    """获取帖子列表（支持分页和话题过滤）"""
    posts = get_post_list(db, skip=skip, limit=limit, topic=topic)
    return {"code": 0, "data": posts}


@router.get("/{post_id}", response_model=PostResponse)
async def get_post_detail(
    post_id: str,
    db: Session = Depends(get_db)
):
    """获取帖子详情"""
    post = get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    return {"code": 0, "data": post}


@router.put("/{post_id}", response_model=PostResponse)
async def update_post_endpoint(
    post_id: str,
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """编辑帖子（仅作者）"""
    update_data = {"content": post_data.content, "topic": post_data.topic}
    post = update_post(db, post_id, current_user.user_id, update_data)
    if not post:
        raise HTTPException(status_code=403, detail="无权限编辑此帖子")
    return {"code": 0, "data": post}


@router.delete("/{post_id}")
async def delete_post_endpoint(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除帖子（仅作者，软删除）"""
    success = delete_post(db, post_id, current_user.user_id)
    if not success:
        raise HTTPException(status_code=403, detail="无权限删除此帖子")
    return {"code": 0, "message": "删除成功"}
```

- [ ] **Step 4: 在 main.py 中注册路由**

```python
# app/main.py (添加)
from app.api.v1.posts import router as posts_router

# 注册帖子路由
app.include_router(posts_router, prefix="/api/v1/posts", tags=["Posts"])
```

- [ ] **Step 5: 运行测试验证通过**

```bash
pytest tests/test_posts_api.py -v
```
Expected: PASS

- [ ] **Step 6: 提交代码**

```bash
git add app/api/v1/posts.py app/main.py tests/test_posts_api.py
git commit -m "feat(posts): add posts API endpoints with full CRUD"
```

---

## Chunk 2: 评论功能

### Task 2.1: 实现评论服务层 - 创建评论

**Files:**
- Modify: `app/services/post_service.py`
- Test: `tests/test_comments.py::test_create_comment`

- [ ] **Step 1: 编写创建评论测试**

```python
# tests/test_comments.py
from app.services.post_service import create_comment, get_comments_by_post

def test_create_comment(db: Session, test_user: User):
    """测试创建评论"""
    post = create_post(db, test_user.user_id, PostCreate(content="测试帖子", topic="技术转行"))

    comment = create_comment(db, test_user.user_id, post.post_id, "这是第一条评论")

    assert comment.content == "这是第一条评论"
    assert comment.post_id == post.post_id
    assert comment.agent_id == test_user.user_id
    assert comment.parent_comment_id is None
    assert comment.is_deleted == False

    # 验证帖子评论数增加
    db.refresh(post)
    assert post.comments_count == 1

def test_create_nested_reply(db: Session, test_user: User):
    """测试创建嵌套回复"""
    post = create_post(db, test_user.user_id, PostCreate(content="测试帖子", topic="技术转行"))

    # 创建父评论
    parent = create_comment(db, test_user.user_id, post.post_id, "父评论")

    # 回复父评论
    reply = create_comment(db, test_user.user_id, post.post_id, "回复", parent.post_id)

    assert reply.parent_comment_id == parent.comment_id
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_comments.py::test_create_comment -v
```
Expected: FAIL

- [ ] **Step 3: 实现创建评论服务**

```python
# app/services/post_service.py (续)
from app.models.comment import Comment

def create_comment(
    db: Session,
    agent_id: str,
    post_id: str,
    content: str,
    parent_comment_id: Optional[str] = None
) -> Comment:
    """
    创建评论（支持嵌套回复）

    Args:
        db: 数据库会话
        agent_id: 用户/Agent ID
        post_id: 帖子 ID
        content: 评论内容
        parent_comment_id: 可选的父评论 ID（用于回复）

    Returns:
        创建的 Comment 对象
    """
    # 验证帖子存在
    post = get_post_by_id(db, post_id)
    if not post:
        raise ValueError("帖子不存在")

    comment = Comment(
        comment_id=f"comment_{uuid.uuid4().hex}",
        post_id=post_id,
        agent_id=agent_id,
        parent_comment_id=parent_comment_id,
        content=content,
        is_deleted=False
    )

    db.add(comment)

    # 更新帖子评论数
    post.comments_count += 1
    db.commit()
    db.refresh(comment)

    return comment
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_comments.py::test_create_comment -v
```
Expected: PASS

- [ ] **Step 5: 提交代码**

```bash
git add app/services/post_service.py tests/test_comments.py
git commit -m "feat(comments): add create_comment with nested reply support"
```

---

### Task 2.2: 实现评论服务层 - 获取评论列表

**Files:**
- Modify: `app/services/post_service.py`
- Test: `tests/test_comments.py::test_get_comments_by_post`

- [ ] **Step 1: 编写获取评论测试**

```python
# tests/test_comments.py
def test_get_comments_by_post(db: Session, test_user: User):
    """测试获取帖子评论列表"""
    post = create_post(db, test_user.user_id, PostCreate(content="测试帖子", topic="技术转行"))

    # 创建多条评论
    c1 = create_comment(db, test_user.user_id, post.post_id, "评论 1")
    c2 = create_comment(db, test_user.user_id, post.post_id, "评论 2")
    c3 = create_comment(db, test_user.user_id, post.post_id, "评论 3")

    # 获取评论（按时间正序）
    comments = get_comments_by_post(db, post.post_id)

    assert len(comments) == 3
    assert comments[0].comment_id == c1.comment_id
    assert comments[1].comment_id == c2.comment_id
    assert comments[2].comment_id == c3.comment_id

    # 验证不返回已删除评论
    c2.is_deleted = True
    db.commit()

    comments = get_comments_by_post(db, post.post_id)
    assert len(comments) == 2
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_comments.py::test_get_comments_by_post -v
```
Expected: FAIL

- [ ] **Step 3: 实现获取评论服务**

```python
# app/services/post_service.py (续)

def get_comments_by_post(db: Session, post_id: str) -> List[Comment]:
    """
    获取帖子的所有评论（按创建时间正序，不包括已删除）

    Args:
        db: 数据库会话
        post_id: 帖子 ID

    Returns:
        Comment 对象列表
    """
    return db.query(Comment).filter(
        Comment.post_id == post_id,
        Comment.is_deleted == False
    ).order_by(Comment.created_at.asc()).all()
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_comments.py::test_get_comments_by_post -v
```
Expected: PASS

- [ ] **Step 5: 提交代码**

```bash
git add app/services/post_service.py tests/test_comments.py
git commit -m "feat(comments): add get_comments_by_post ordered by creation time"
```

---

### Task 2.3: 实现评论服务层 - 删除评论

**Files:**
- Modify: `app/services/post_service.py`
- Test: `tests/test_comments.py::test_delete_comment`

- [ ] **Step 1: 编写删除评论测试**

```python
# tests/test_comments.py
def test_delete_comment(db: Session, test_user: User):
    """测试删除评论"""
    post = create_post(db, test_user.user_id, PostCreate(content="测试帖子", topic="技术转行"))
    comment = create_comment(db, test_user.user_id, post.post_id, "要删除的评论")

    # 删除评论
    result = delete_comment(db, comment.comment_id, test_user.user_id)

    assert result == True

    # 验证软删除
    db.refresh(comment)
    assert comment.is_deleted == True

    # 验证不再返回列表
    comments = get_comments_by_post(db, post.post_id)
    assert len(comments) == 0

    # 验证删除他人评论失败
    comment2 = create_comment(db, test_user.user_id, post.post_id, "评论 2")
    other_user = create_test_user(db)
    result2 = delete_comment(db, comment2.comment_id, other_user.user_id)
    assert result2 == False
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_comments.py::test_delete_comment -v
```
Expected: FAIL

- [ ] **Step 3: 实现删除评论服务**

```python
# app/services/post_service.py (续)

def delete_comment(db: Session, comment_id: str, agent_id: str) -> bool:
    """
    删除评论（软删除，仅作者可删除）

    Args:
        db: 数据库会话
        comment_id: 评论 ID
        agent_id: 用户/Agent ID

    Returns:
        删除成功返回 True，失败返回 False
    """
    comment = db.query(Comment).filter(
        Comment.comment_id == comment_id
    ).first()

    if not comment or comment.agent_id != agent_id:
        return False

    comment.is_deleted = True

    # 更新帖子评论数
    post = get_post_by_id(db, comment.post_id)
    if post:
        post.comments_count = max(0, post.comments_count - 1)

    db.commit()
    return True
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_comments.py::test_delete_comment -v
```
Expected: PASS

- [ ] **Step 5: 提交代码**

```bash
git add app/services/post_service.py tests/test_comments.py
git commit -m "feat(comments): add delete_comment with permission check"
```

---

### Task 2.4: 实现评论 API 路由

**Files:**
- Create: `app/api/v1/comments.py`
- Test: `tests/test_comments_api.py`

- [ ] **Step 1: 编写评论 API 测试**

```python
# tests/test_comments_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_comment_api(auth_headers: dict):
    """测试评论帖子 API"""
    # 先创建帖子
    post_resp = client.post("/api/v1/posts/", headers=auth_headers,
                            json={"content": "测试帖子", "topic": "测试"})
    post_id = post_resp.json()["data"]["post_id"]

    # 评论
    response = client.post(
        f"/api/v1/posts/{post_id}/comments",
        headers=auth_headers,
        json={"content": "这是评论"}
    )

    assert response.status_code == 200
    assert response.json()["code"] == 0
    assert response.json()["data"]["content"] == "这是评论"

def test_create_reply_api(auth_headers: dict):
    """测试回复评论 API"""
    post_resp = client.post("/api/v1/posts/", headers=auth_headers,
                            json={"content": "测试帖子", "topic": "测试"})
    post_id = post_resp.json()["data"]["post_id"]

    # 创建父评论
    parent_resp = client.post(f"/api/v1/posts/{post_id}/comments",
                              headers=auth_headers,
                              json={"content": "父评论"})
    parent_id = parent_resp.json()["data"]["comment_id"]

    # 回复
    reply_resp = client.post(f"/api/v1/posts/{post_id}/comments",
                             headers=auth_headers,
                             json={"content": "回复", "parent_comment_id": parent_id})

    assert reply_resp.status_code == 200
    assert reply_resp.json()["data"]["parent_comment_id"] == parent_id

def test_get_comments_api(auth_headers: dict):
    """测试获取评论列表 API"""
    post_resp = client.post("/api/v1/posts/", headers=auth_headers,
                            json={"content": "测试帖子", "topic": "测试"})
    post_id = post_resp.json()["data"]["post_id"]

    # 创建几条评论
    client.post(f"/api/v1/posts/{post_id}/comments", headers=auth_headers,
                json={"content": "评论 1"})
    client.post(f"/api/v1/posts/{post_id}/comments", headers=auth_headers,
                json={"content": "评论 2"})

    # 获取评论
    response = client.get(f"/api/v1/posts/{post_id}/comments")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 2

def test_delete_comment_api(auth_headers: dict):
    """测试删除评论 API"""
    post_resp = client.post("/api/v1/posts/", headers=auth_headers,
                            json={"content": "测试帖子", "topic": "测试"})
    post_id = post_resp.json()["data"]["post_id"]

    comment_resp = client.post(f"/api/v1/posts/{post_id}/comments",
                               headers=auth_headers,
                               json={"content": "要删除的评论"})
    comment_id = comment_resp.json()["data"]["comment_id"]

    # 删除
    response = client.delete(f"/api/v1/posts/{post_id}/comments/{comment_id}",
                             headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["code"] == 0
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_comments_api.py -v
```
Expected: FAIL

- [ ] **Step 3: 实现评论 API 路由**

```python
# app/api/v1/comments.py
"""评论 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import Optional

from app.core.auth import get_current_user
from app.models.user import User
from app.services.post_service import create_comment, get_comments_by_post, delete_comment
from app.schemas.post import CommentCreate, CommentResponse
from app.database import get_db

router = APIRouter()


@router.post("/posts/{post_id}/comments", response_model=CommentResponse)
async def create_post_comment(
    post_id: str = Path(..., description="帖子 ID"),
    comment_data: CommentCreate = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """评论帖子（支持嵌套回复）"""
    try:
        comment = create_comment(
            db,
            current_user.user_id,
            post_id,
            comment_data.content,
            comment_data.parent_comment_id
        )
        return {"code": 0, "data": comment}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/posts/{post_id}/comments", response_model=list[CommentResponse])
async def list_post_comments(
    post_id: str = Path(..., description="帖子 ID"),
    db: Session = Depends(get_db)
):
    """获取帖子的所有评论（按时间正序）"""
    comments = get_comments_by_post(db, post_id)
    return {"code": 0, "data": comments}


@router.delete("/posts/{post_id}/comments/{comment_id}")
async def delete_post_comment(
    post_id: str = Path(..., description="帖子 ID"),
    comment_id: str = Path(..., description="评论 ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除评论（仅作者）"""
    success = delete_comment(db, comment_id, current_user.user_id)
    if not success:
        raise HTTPException(status_code=403, detail="无权限删除此评论")
    return {"code": 0, "message": "删除成功"}
```

- [ ] **Step 4: 在 main.py 中注册评论路由**

```python
# app/main.py (添加)
from app.api.v1.comments import router as comments_router

# 注册评论路由
app.include_router(comments_router, prefix="/api/v1", tags=["Comments"])
```

- [ ] **Step 5: 运行测试验证通过**

```bash
pytest tests/test_comments_api.py -v
```
Expected: PASS

- [ ] **Step 6: 提交代码**

```bash
git add app/api/v1/comments.py app/main.py tests/test_comments_api.py
git commit -m "feat(comments): add comments API endpoints"
```

---

## Chunk 3: 点赞功能与最终整合

### Task 3.1: 实现点赞服务层

**Files:**
- Modify: `app/services/post_service.py`
- Test: `tests/test_post_likes.py`

- [ ] **Step 1: 检查数据模型**

首先确认 `likes` 表或 `Post.likes_count` 字段是否存在：

```bash
# 查看 models 目录
ls app/models/
# 查看 Post 模型
cat app/models/post.py
```

- [ ] **Step 2: 编写点赞测试**

```python
# tests/test_post_likes.py
from app.services.post_service import like_post, unlike_post, has_liked

def test_like_post(db: Session, test_user: User):
    """测试点赞帖子"""
    post = create_post(db, test_user.user_id, PostCreate(content="测试帖子", topic="技术转行"))

    # 点赞
    result = like_post(db, post.post_id, test_user.user_id)
    assert result == True

    # 验证点赞数增加
    db.refresh(post)
    assert post.likes_count == 1

    # 验证已点赞状态
    assert has_liked(db, post.post_id, test_user.user_id) == True

    # 重复点赞应该返回 False 或不增加计数
    result2 = like_post(db, post.post_id, test_user.user_id)
    assert result2 == False  # 或 True 但 likes_count 不增加

def test_unlike_post(db: Session, test_user: User):
    """测试取消点赞"""
    post = create_post(db, test_user.user_id, PostCreate(content="测试帖子", topic="技术转行"))

    # 先点赞
    like_post(db, post.post_id, test_user.user_id)

    # 取消点赞
    result = unlike_post(db, post.post_id, test_user.user_id)
    assert result == True

    # 验证点赞数减少
    db.refresh(post)
    assert post.likes_count == 0

    # 验证已取消点赞状态
    assert has_liked(db, post.post_id, test_user.user_id) == False
```

- [ ] **Step 3: 运行测试验证失败**

```bash
pytest tests/test_post_likes.py -v
```
Expected: FAIL

- [ ] **Step 4: 实现点赞服务（根据实际数据模型调整）**

**方案 A：如果有独立 likes 表**

```python
# app/services/post_service.py (续)
from app.models.like import Like  # 假设有 Like 模型

def like_post(db: Session, post_id: str, agent_id: str) -> bool:
    """
    点赞帖子（防止重复点赞）
    """
    post = get_post_by_id(db, post_id)
    if not post:
        return False

    # 检查是否已点赞
    existing = db.query(Like).filter(
        Like.post_id == post_id,
        Like.agent_id == agent_id
    ).first()

    if existing:
        return False  # 已点赞过

    like = Like(post_id=post_id, agent_id=agent_id)
    db.add(like)
    post.likes_count += 1
    db.commit()

    return True

def unlike_post(db: Session, post_id: str, agent_id: str) -> bool:
    """取消点赞"""
    like = db.query(Like).filter(
        Like.post_id == post_id,
        Like.agent_id == agent_id
    ).first()

    if not like:
        return False

    db.delete(like)
    post = get_post_by_id(db, post_id)
    if post:
        post.likes_count = max(0, post.likes_count - 1)
    db.commit()

    return True

def has_liked(db: Session, post_id: str, agent_id: str) -> bool:
    """检查是否已点赞"""
    return db.query(Like).filter(
        Like.post_id == post_id,
        Like.agent_id == agent_id
    ).first() is not None
```

**方案 B：如果只有 likes_count 字段（简化版）**

```python
# app/services/post_service.py (续)
# 简化版：不防止重复点赞，仅用于 MVP

def like_post(db: Session, post_id: str, agent_id: str) -> bool:
    """点赞帖子（简化版，不检查重复）"""
    post = get_post_by_id(db, post_id)
    if not post:
        return False

    post.likes_count += 1
    db.commit()
    return True

def unlike_post(db: Session, post_id: str, agent_id: str) -> bool:
    """取消点赞（简化版）"""
    post = get_post_by_id(db, post_id)
    if not post or post.likes_count <= 0:
        return False

    post.likes_count -= 1
    db.commit()
    return True

def has_liked(db: Session, post_id: str, agent_id: str) -> bool:
    """简化版：始终返回 False"""
    return False  # TODO: 实现完整的点赞追踪
```

- [ ] **Step 5: 运行测试验证通过**

```bash
pytest tests/test_post_likes.py -v
```
Expected: PASS

- [ ] **Step 6: 提交代码**

```bash
git add app/services/post_service.py tests/test_post_likes.py
git commit -m "feat(posts): add like/unlike functionality"
```

---

### Task 3.2: 实现点赞 API 端点

**Files:**
- Modify: `app/api/v1/posts.py`
- Test: `tests/test_posts_api.py::test_like_post_api`

- [ ] **Step 1: 添加点赞 API 测试**

```python
# tests/test_posts_api.py (追加)
def test_like_post_api(auth_headers: dict):
    """测试点赞 API"""
    post_resp = client.post("/api/v1/posts/", headers=auth_headers,
                            json={"content": "测试帖子", "topic": "测试"})
    post_id = post_resp.json()["data"]["post_id"]

    # 点赞
    response = client.post(f"/api/v1/posts/{post_id}/like", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["code"] == 0

    # 验证点赞数
    get_resp = client.get(f"/api/v1/posts/{post_id}")
    assert get_resp.json()["data"]["likes_count"] == 1

def test_unlike_post_api(auth_headers: dict):
    """测试取消点赞 API"""
    post_resp = client.post("/api/v1/posts/", headers=auth_headers,
                            json={"content": "测试帖子", "topic": "测试"})
    post_id = post_resp.json()["data"]["post_id"]

    # 先点赞
    client.post(f"/api/v1/posts/{post_id}/like", headers=auth_headers)

    # 取消点赞
    response = client.post(f"/api/v1/posts/{post_id}/unlike", headers=auth_headers)
    assert response.status_code == 200

    # 验证点赞数为 0
    get_resp = client.get(f"/api/v1/posts/{post_id}")
    assert get_resp.json()["data"]["likes_count"] == 0
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_posts_api.py::test_like_post_api -v
```
Expected: FAIL

- [ ] **Step 3: 添加点赞 API 端点**

```python
# app/api/v1/posts.py (追加)
from app.services.post_service import like_post, unlike_post, has_liked

@router.post("/{post_id}/like")
async def like_post_endpoint(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """点赞帖子"""
    success = like_post(db, post_id, current_user.user_id)
    if not success:
        raise HTTPException(status_code=400, detail="点赞失败或已点赞过")
    return {"code": 0, "message": "点赞成功"}


@router.post("/{post_id}/unlike")
async def unlike_post_endpoint(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消点赞"""
    success = unlike_post(db, post_id, current_user.user_id)
    if not success:
        raise HTTPException(status_code=400, detail="取消点赞失败")
    return {"code": 0, "message": "已取消点赞"}


@router.get("/{post_id}/like-status")
async def get_like_status(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取点赞状态"""
    liked = has_liked(db, post_id, current_user.user_id)
    return {"code": 0, "data": {"liked": liked}}
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_posts_api.py::test_like_post_api -v
```
Expected: PASS

- [ ] **Step 5: 提交代码**

```bash
git add app/api/v1/posts.py tests/test_posts_api.py
git commit -m "feat(posts): add like/unlike/like-status API endpoints"
```

---

### Task 3.3: 运行完整模块测试

**Files:**
- 全部测试文件

- [ ] **Step 1: 运行所有帖子相关测试**

```bash
# 运行所有帖子和评论测试
pytest tests/test_posts.py tests/test_posts_api.py tests/test_comments.py tests/test_comments_api.py tests/test_post_likes.py -v
```

Expected: ALL PASS

- [ ] **Step 2: 检查代码风格**

```bash
# 如果有配置 linting
ruff check app/services/post_service.py app/api/v1/posts.py app/api/v1/comments.py
```

- [ ] **Step 3: 提交最终整合代码**

```bash
git add .
git commit -m "feat(module2): complete posts & comments system with full test coverage"
```

---

## 模块 2 完成检查清单

- [ ] 帖子 CRUD 功能全部实现并测试通过
- [ ] 评论（含嵌套回复）功能全部实现并测试通过
- [ ] 点赞功能全部实现并测试通过
- [ ] 所有 API 端点可正常访问
- [ ] 权限验证正常工作（只能编辑/删除自己的内容）
- [ ] 软删除逻辑正确
- [ ] 测试覆盖率达标

---

## API 端点汇总

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/posts/` | 发布帖子 | ✅ |
| GET | `/api/v1/posts/` | 获取帖子列表 | ❌ |
| GET | `/api/v1/posts/{post_id}` | 获取帖子详情 | ❌ |
| PUT | `/api/v1/posts/{post_id}` | 编辑帖子 | ✅ |
| DELETE | `/api/v1/posts/{post_id}` | 删除帖子 | ✅ |
| POST | `/api/v1/posts/{post_id}/like` | 点赞 | ✅ |
| POST | `/api/v1/posts/{post_id}/unlike` | 取消点赞 | ✅ |
| GET | `/api/v1/posts/{post_id}/like-status` | 获取点赞状态 | ✅ |
| POST | `/api/v1/posts/{post_id}/comments` | 评论/回复 | ✅ |
| GET | `/api/v1/posts/{post_id}/comments` | 获取评论列表 | ❌ |
| DELETE | `/api/v1/posts/{post_id}/comments/{comment_id}` | 删除评论 | ✅ |

---

计划完成。准备好开始执行了吗？
