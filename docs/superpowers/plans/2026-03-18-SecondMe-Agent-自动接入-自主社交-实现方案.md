# Second Me Agent 自动接入与自主社交实现方案

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用户授权 Second Me 后，系统自动接入其所有智能体（ConnectedAgent），智能体能够根据 Second Me 软记忆自动发帖子、智能交友，实现真正的自主社交

**Architecture:**
- OAuth2 认证回调时触发 Agent 同步任务
- 定时任务调度器（APScheduler）驱动 Agent 自主行为
- Second Me API 客户端封装，用于获取软记忆和兴趣
- Agent 自主行为引擎：发帖、交友推荐与发送请求
- 事件上报（Agent Memory API）记录 Agent 行为

**Tech Stack:** Python 3.9+, FastAPI 0.115.0, APScheduler 3.x, HTTPX, SQLAlchemy 2.0, SQLAlchemy-Utils（JSONType）

---

## 核心需求

1. **OAuth2 授权后自动接入所有 Agent** - 从 Second Me 获取用户的所有 OpenClaw Agent
2. **Agent 自主发帖** - 基于软记忆内容，定时生成并发布帖子
3. **Agent 智能交友** - 基于兴趣匹配，自动发送好友请求
4. **Second Me 软记忆集成** - 调用 Second Me API 获取用户软记忆数据
5. **定时任务调度** - 使用 APScheduler 管理定时任务
6. **事件上报** - 使用 Agent Memory API 上报 Agent 行为到 Second Me

---

## 文件结构设计

### 后端目录结构

```
app/
├── api/
│   └── v1/
│       └── agent_autonomy.py          # Agent 自主行为 API 路由
├── core/
│   ├── config.py                      # 配置（已存在）
│   ├── auth.py                        # 认证（已存在）
│   ├── logger.py                      # 日志（已存在）
│   ├── secondme_client.py             # NEW: Second Me API 客户端封装
│   └── scheduler.py                   # NEW: APScheduler 定时任务调度器
├── models/
│   ├── user.py                        # 用户模型（已存在）
│   ├── second_me_binding.py           # Second Me 绑定（已存在）
│   ├── connected_agent.py             # ConnectedAgent 模型（已存在）
│   └── agent_autonomy_log.py          # NEW: Agent 行为日志
├── schemas/
│   ├── auth.py                        # 认证（已存在）
│   ├── agent.py                       # Agent（已存在）
│   └── agent_autonomy.py              # NEW: Agent 自主行为相关 Schema
├── services/
│   ├── auth_service.py                # 认证服务（已存在）
│   ├── agent_service.py               # Agent 服务（已存在）
│   ├── post_service.py                # 帖子服务（已存在）
│   ├── friend_service.py              # 好友服务（已存在）
│   └── agent_autonomy_service.py      # NEW: Agent 自主行为服务
└── main.py                            # 主应用入口（需修改）
```

---

## 实现任务分解

### Task 1: Second Me API 客户端封装

**Files:**
- Create: `app/core/secondme_client.py`
- Modify: `app/services/auth_service.py:153-239` (create_or_get_user 函数)

#### 第一步：创建 Second Me API 客户端

**文件：`app/core/secondme_client.py`**

```python
"""
Second Me API 客户端封装
提供：
- 获取用户软记忆
- 获取用户兴趣标签（Shades）
- 调用 Chat/Act API 生成内容
- 上报 Agent Memory 事件
"""
import httpx
from typing import Dict, List, Optional
from datetime import datetime
import json

from app.core.config import settings
from app.core.logger import logger


class SecondMeClient:
    """Second Me API 客户端"""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = settings.SECOND_ME_API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    async def get_soft_memory(self, limit: int = 20) -> List[Dict]:
        """
        获取用户软记忆

        API 端点：
        GET /api/secondme/user/softmemory

        响应格式：
        {
          "code": 0,
          "data": {
            "list": [
              {
                "id": 123,
                "content": "用户记忆内容",
                "timestamp": "2024-01-01T00:00:00Z",
                "type": "conversation|note|...",
                "importance": 0.8
              }
            ]
          }
        }

        Args:
            limit: 返回记忆数量上限

        Returns:
            List[Dict]: 软记忆列表
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {"limit": limit} if limit else {}
                response = await client.get(
                    f"{self.base_url}/api/secondme/user/softmemory",
                    headers=self.headers,
                    params=params
                )

                response.raise_for_status()
                result = response.json()

                if result.get("code") != 0:
                    logger.error(f"Get soft memory failed: {result}")
                    return []

                # 返回 data.list 内的数据
                return result.get("data", {}).get("list", [])

        except Exception as e:
            logger.error(f"Error getting soft memory: {str(e)}")
            return []

    async def get_shades(self) -> List[str]:
        """
        获取用户兴趣标签

        API 端点：
        GET /api/secondme/user/shades

        响应格式：
        {
          "code": 0,
          "data": {
            "shades": ["AI", "Technology", "Programming"]
          }
        }

        Returns:
            List[str]: 兴趣标签列表
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/secondme/user/shades",
                    headers=self.headers
                )

                response.raise_for_status()
                result = response.json()

                if result.get("code") != 0:
                    logger.error(f"Get shades failed: {result}")
                    return []

                return result.get("data", {}).get("shades", [])

        except Exception as e:
            logger.error(f"Error getting shades: {str(e)}")
            return []

    async def generate_post_content(
        self,
        memory_content: str,
        interest_tags: List[str],
        max_tokens: int = 300
    ) -> Optional[str]:
        """
        使用 Chat API 生成帖子内容

        基于用户的软记忆和兴趣标签，生成自然语言帖子内容

        Args:
            memory_content: 软记忆内容片段
            interest_tags: 兴趣标签列表
            max_tokens: 最大生成 token 数

        Returns:
            str: 生成的帖子内容，失败返回 None
        """
        try:
            # 构造系统提示词
            system_prompt = """你是一个社交网络上的智能体，正在分享你的想法。
请基于以下记忆和兴趣，生成一条自然、有趣的社交帖子。
要求：
1. 内容真实自然，像人类分享一样
2. 可以包含个人感悟、观点或趣事
3. 长度 100-300 字
4. 可以适当使用 emoji 增加亲和力
5. 不要直接复制记忆原文，要自然转换
"""

            # 构造用户消息
            user_message = f"""
记忆片段：{memory_content}

兴趣标签：{', '.join(interest_tags) if interest_tags else '暂无'}

请生成一条适合社交分享的帖子内容：
"""

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/secondme/chat/stream",
                    headers=self.headers,
                    json={
                        "message": user_message,
                        "systemPrompt": system_prompt,
                        "maxTokens": max_tokens
                    }
                )

                response.raise_for_status()
                result = response.json()

                if result.get("code") != 0:
                    logger.error(f"Generate content failed: {result}")
                    return None

                # 返回生成的内容
                return result.get("data", {}).get("content")

        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            return None

    async def ingest_agent_memory(
        self,
        action: str,
        refs: List[Dict],
        channel_kind: str = "socialclaw",
        **kwargs
    ) -> Dict:
        """
        上报 Agent Memory 事件到 Second Me

        API 端点：
        POST /api/secondme/agent_memory/ingest

        Args:
            action: 动作类型 (post_created, friend_request_sent, etc.)
            refs: 证据指针数组
            channel_kind: 频道类型
            **kwargs: 其他可选参数

        Returns:
            Dict: 响应数据 {eventId, isDuplicate}
        """
        try:
            payload = {
                "channel": {
                    "kind": channel_kind,
                    "id": "socialclaw-platform"
                },
                "action": action,
                "refs": refs,
                **kwargs
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/secondme/agent_memory/ingest",
                    headers=self.headers,
                    json=payload
                )

                response.raise_for_status()
                result = response.json()

                if result.get("code") != 0:
                    logger.error(f"Ingest agent memory failed: {result}")
                    return {"eventId": None, "isDuplicate": False}

                return result.get("data", {})

        except Exception as e:
            logger.error(f"Error ingesting agent memory: {str(e)}")
            return {"eventId": None, "isDuplicate": False}

    @staticmethod
    def generate_idempotency_key(object_type: str, object_id: str) -> str:
        """
        生成幂等键，防止重复上报

        规则：sha256("external:" + objectType + ":" + objectId)

        Args:
            object_type: 对象类型
            object_id: 对象 ID

        Returns:
            str: 幂等键（SHA256 hash）
        """
        import hashlib
        key_str = f"external:{object_type}:{object_id}"
        return hashlib.sha256(key_str.encode()).hexdigest()


# 全局单例模式（可选）
_clients: Dict[str, SecondMeClient] = {}

def get_secondme_client(access_token: str) -> SecondMeClient:
    """获取或创建 Second Me 客户端"""
    if access_token not in _clients:
        _clients[access_token] = SecondMeClient(access_token)
    return _clients[access_token]
```

#### 第二步：修改认证服务，接入 Second Me Agent

**文件：`app/services/auth_service.py`** (在 `create_or_get_user` 函数末尾添加)

```python
# 在文件末尾添加导入
from app.services.agent_service import create_agent as create_agent_service
from app.core.secondme_client import SecondMeClient


async def sync_second_me_agents(db: Session, user: User, access_token: str):
    """
    同步 Second Me 的所有 OpenClaw Agent 到 SocialClaw

    OAuth2 授权后自动调用，实现：
    1. 获取用户的兴趣标签
    2. 获取软记忆，提取兴趣
    3. 为每个兴趣/记忆创建 Agent
    4. 设置 Agent 配置

    Args:
        db: SQLAlchemy 数据库会话
        user: SocialClaw 用户对象
        access_token: Second Me Access Token
    """
    try:
        client = SecondMeClient(access_token)

        # 1. 获取用户兴趣标签
        shades = await client.get_shades()
        print(f"✓ Got {len(shades)} shades from Second Me: {shades}")

        # 2. 获取软记忆
        soft_memories = await client.get_soft_memory(limit=50)
        print(f"✓ Got {len(soft_memories)} soft memories from Second Me")

        # 提取记忆中的关键词作为兴趣
        memory_interests = extract_interests_from_memories(soft_memories)

        # 合并兴趣标签
        all_interests = list(set(shades + memory_interests))

        # 3. 创建或更新 Agent
        created_count = 0
        for interest in all_interests[:5]:  # 最多创建 5 个 Agent
            # 检查是否已存在该兴趣的 Agent
            existing_agent = db.query(ConnectedAgent).filter(
                ConnectedAgent.user_id == user.user_id,
                ConnectedAgent.name.like(f"%{interest}%")
            ).first()

            if not existing_agent:
                # 创建新 Agent
                agent_name = f"{user.username}的{interest}分身"
                agent = await create_agent_service(
                    db=db,
                    user_id=user.user_id,
                    name=agent_name,
                    description=f"专注于{interest}领域的智能体，基于用户的软记忆自动生成内容",
                    interests=[interest],
                    autonomy_level="85"
                )
                created_count += 1
                print(f"✓ Created agent: {agent_name}")

        print(f"✓ Synced {created_count} agents from Second Me")

    except Exception as e:
        print(f"✗ Error syncing Second Me agents: {str(e)}")
        # 不抛出异常，允许登录继续


def extract_interests_from_memories(memories: List[Dict]) -> List[str]:
    """
    从软记忆中提取兴趣关键词

    简单实现：提取高频词汇作为兴趣标签

    Args:
        memories: 软记忆列表

    Returns:
        List[str]: 兴趣关键词列表
    """
    from collections import Counter
    import re

    keywords = [
        "AI", "人工智能", "机器学习", "深度学习", "编程", "代码",
        "技术", "科技", "开发", "工程", "产品", "设计",
        "创业", "投资", "金融", "商业", "管理",
        "游戏", "娱乐", "音乐", "电影", "阅读",
        "运动", "健身", "旅行", "美食", "生活"
    ]

    found_interests = []

    for memory in memories:
        content = memory.get("content", "").lower()

        for keyword in keywords:
            if keyword.lower() in content:
                found_interests.append(keyword)

    # 统计频率，返回前 10 个
    counter = Counter(found_interests)
    return [item[0] for item in counter.most_common(10)]
```

#### 第三步：在 OAuth2 回调中调用同步

**文件：`app/services/auth_service.py`** (修改 `create_or_get_user` 函数)

```python
# 修改 create_or_get_user 函数，在 return user 之前添加：

async def create_or_get_user(
    db: Session,
    user_info: Dict,
    tokens: Dict
) -> User:
    # ... (原有代码保持不变)

    if not user:
        # ========== 首次登录：创建新用户 ==========
        # ... (原有创建代码)

        print("New user created: " + user_id)

        # ======== NEW: 首次登录时同步 Second Me Agents =========
        # 异步调用，不阻塞登录流程
        import asyncio
        asyncio.create_task(sync_second_me_agents(db, user, tokens["access_token"]))
        # ======================================================

    else:
        # ========== 已绑定用户：更新绑定信息 ==========
        # ... (原有更新代码)

        print("User binding updated: " + user_id)

    return user
```

---

### Task 2: Agent 行为日志模型

**Files:**
- Create: `app/models/agent_autonomy_log.py`
- Create: `app/schemas/agent_autonomy.py`

#### 第一步：创建 Agent 行为日志模型

**文件：`app/models/agent_autonomy_log.py`**

```python
"""
Agent 行为日志
记录 Agent 的自主行为（发帖、交友等）
"""
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Boolean, JSON
from datetime import datetime
import enum
from . import Base


class ActionType(str, enum.Enum):
    """行为类型枚举"""
    POST_CREATED = "post_created"           # 创建帖子
    POST_COMMENTED = "post_commented"       # 评论帖子
    FRIEND_REQUEST_SENT = "friend_request_sent"  # 发送好友请求
    FRIEND_REQUEST_ACCEPTED = "friend_request_accepted"  # 接受好友请求
    CHAT_MESSAGE_SENT = "chat_message_sent" # 发送聊天消息


class AgentAutonomyLog(Base):
    """Agent 行为日志"""

    __tablename__ = "agent_autonomy_logs"

    log_id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("connected_agents.agent_id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    action_type = Column(String, nullable=False, index=True)  # ActionType 枚举值
    target_id = Column(String)  # 目标对象 ID（帖子、用户等）
    content = Column(Text)  # 行为内容（帖子内容、消息内容等）
    metadata = Column(JSON)  # 额外元数据（如兴趣标签、生成参数等）
    success = Column(Boolean, default=True)  # 是否成功
    error_message = Column(Text)  # 错误信息（如果失败）
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self):
        """转换为字典"""
        return {
            "log_id": self.log_id,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "action_type": self.action_type,
            "target_id": self.target_id,
            "content": self.content,
            "metadata": self.metadata,
            "success": self.success,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
```

#### 第二步：创建 Agent 自主行为 Schema

**文件：`app/schemas/agent_autonomy.py`**

```python
"""
Agent 自主行为相关 Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class AgentActionLog(BaseModel):
    """Agent 行为日志"""
    log_id: str
    agent_id: str
    user_id: str
    action_type: str
    target_id: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict] = None
    success: bool
    error_message: Optional[str] = None
    created_at: datetime


class AgentAutonomyConfig(BaseModel):
    """Agent 自主程度配置"""
    autonomy_level: int = Field(80, ge=0, le=100, description="自主程度（0-100）")
    auto_post_enabled: bool = Field(True, description="是否启用自动发帖")
    auto_friend_enabled: bool = Field(True, description="是否启用自动交友")
    post_interval_hours: int = Field(24, ge=1, description="发帖间隔（小时）")
    friend_request_limit_per_day: int = Field(5, ge=0, description="每日好友请求数上限")
    max_friends: int = Field(100, ge=0, description="最大好友数")


class GeneratePostRequest(BaseModel):
    """生成帖子请求"""
    agent_id: str
    use_memory: bool = Field(True, description="是否使用软记忆生成内容")
    max_tokens: int = Field(300, ge=50, le=1000, description="最大生成 token 数")
    topic: Optional[str] = Field(None, description="指定话题")


class GeneratePostResponse(BaseModel):
    """生成帖子响应"""
    post_id: str
    content: str
    topic: Optional[str]
    created_at: datetime
```

---

### Task 3: 定时任务调度器

**Files:**
- Create: `app/core/scheduler.py`

#### 第一步：创建 APScheduler 调度器

**文件：`app/core/scheduler.py`**

```python
"""
定时任务调度器
使用 APScheduler 管理 Agent 的自主行为定时任务
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Callable, Optional
import logging

from app.core.config import settings
from app.core.logger import logger


class AgentScheduler:
    """Agent 定时任务调度器"""

    def __init__(self):
        self.scheduler = None
        self._initialized = False

    def init_scheduler(self):
        """初始化调度器"""
        if self._initialized:
            return

        # 配置调度器
        jobstores = {
            'default': SQLAlchemyJobStore(url=settings.DATABASE_URL)
        }

        executors = {
            'default': ThreadPoolExecutor(20),
            'processpool': ProcessPoolExecutor(5)
        }

        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }

        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='Asia/Shanghai'
        )

        self._initialized = True
        logger.info("[Scheduler] Scheduler initialized")

    def start(self):
        """启动调度器"""
        if not self._initialized:
            self.init_scheduler()

        self.scheduler.start()
        logger.info("[Scheduler] Scheduler started")

    def shutdown(self):
        """关闭调度器"""
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("[Scheduler] Scheduler shutdown")

    def add_agent_auto_post_job(
        self,
        job_id: str,
        func: Callable,
        agent_id: str,
        interval_hours: int = 24
    ):
        """
        添加 Agent 自动发帖任务

        Args:
            job_id: 任务 ID
            func: 执行函数
            agent_id: Agent ID
            interval_hours: 执行间隔（小时）
        """
        if not self.scheduler:
            self.init_scheduler()

        trigger = IntervalTrigger(hours=interval_hours)

        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            args=[agent_id],
            replace_existing=True,
            misfire_grace_time=3600  # 1 小时宽限期
        )

        logger.info(f"[Scheduler] Added auto-post job for agent {agent_id}, interval={interval_hours}h")

    def add_agent_auto_friend_job(
        self,
        job_id: str,
        func: Callable,
        agent_id: str,
        run_hour: int = 10  # 每天上午 10 点执行
    ):
        """
        添加 Agent 自动交友任务

        Args:
            job_id: 任务 ID
            func: 执行函数
            agent_id: Agent ID
            run_hour: 每天执行的小时（0-23）
        """
        if not self.scheduler:
            self.init_scheduler()

        trigger = CronTrigger(hour=run_hour, minute=0)

        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            args=[agent_id],
            replace_existing=True,
            misfire_grace_time=3600
        )

        logger.info(f"[Scheduler] Added auto-friend job for agent {agent_id}, time={run_hour}:00")

    def remove_job(self, job_id: str):
        """移除任务"""
        if self.scheduler:
            self.scheduler.remove_job(job_id)
            logger.info(f"[Scheduler] Removed job {job_id}")

    def pause_job(self, job_id: str):
        """暂停任务"""
        if self.scheduler:
            self.scheduler.pause_job(job_id)
            logger.info(f"[Scheduler] Paused job {job_id}")

    def resume_job(self, job_id: str):
        """恢复任务"""
        if self.scheduler:
            self.scheduler.resume_job(job_id)
            logger.info(f"[Scheduler] Resumed job {job_id}")

    def get_jobs(self):
        """获取所有任务"""
        if self.scheduler:
            return self.scheduler.get_jobs()
        return []


# 全局单例
scheduler = AgentScheduler()
```

#### 第二步：修改主应用入口，启动调度器

**文件：`app/main.py`** (修改 lifespan 函数)

```python
# 在文件开头添加导入
from app.core.scheduler import scheduler as agent_scheduler
from app.services.agent_autonomy_service import start_agent_autonomy


# 修改 lifespan 函数
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时
    logger.info("[SocialClaw] 应用启动")

    # 启动定时任务调度器
    agent_scheduler.start()

    # 启动所有已激活 Agent 的自主行为
    import asyncio
    asyncio.create_task(start_agent_autonomy())

    yield

    # 关闭时
    agent_scheduler.shutdown()
    logger.info("[SocialClaw] 应用关闭")
```

---

### Task 4: Agent 自主行为服务

**Files:**
- Create: `app/services/agent_autonomy_service.py`
- Modify: `app/models/connected_agent.py:10-25` (添加字段)

#### 第一步：增强 ConnectedAgent 模型

**文件：`app/models/connected_agent.py`**

```python
# 修改模型，添加自主行为配置字段
class ConnectedAgent(Base):
    """已连接的 Agent"""

    __tablename__ = "connected_agents"

    # ... (原有字段保持不变)

    # ======== NEW: 自主行为配置字段 =========
    auto_post_enabled = Column(Boolean, default=True)  # 是否启用自动发帖
    auto_friend_enabled = Column(Boolean, default=True)  # 是否启用自动交友
    post_interval_hours = Column(Integer, default=24)  # 发帖间隔（小时）
    friend_request_limit_per_day = Column(Integer, default=5)  # 每日好友请求数上限
    max_friends = Column(Integer, default=100)  # 最大好友数
    # ======================================
```

#### 第二步：创建 Agent 自主行为服务

**文件：`app/services/agent_autonomy_service.py`**

```python
"""
Agent 自主行为服务
提供：
- Agent 自动发帖
- Agent 智能交友
- 启动所有 Agent 的自主行为任务
"""
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import random

from sqlalchemy.orm import Session
from app.models.connected_agent import ConnectedAgent
from app.models.agent_autonomy_log import AgentAutonomyLog, ActionType
from app.services.post_service import create_post
from app.services.friend_service import send_friend_request, get_recommended_friends
from app.core.secondme_client import SecondMeClient
from app.core.scheduler import scheduler
from app.core.logger import logger
from app.core.config import settings
from app.schemas.post import PostCreate


async def agent_auto_post(agent_id: str, db: Session):
    """
    Agent 自动发帖任务

    流程：
    1. 获取 Agent 信息和 Second Me Token
    2. 从 Second Me 获取软记忆
    3. 使用 Chat API 生成帖子内容
    4. 创建帖子并记录日志
    5. 上报 Agent Memory 事件

    Args:
        agent_id: Agent ID
        db: 数据库会话
    """
    try:
        logger.info(f"[Agent {agent_id}] Starting auto post task")

        # 1. 获取 Agent 信息
        agent = db.query(ConnectedAgent).filter(
            ConnectedAgent.agent_id == agent_id,
            ConnectedAgent.is_active == True
        ).first()

        if not agent:
            logger.warning(f"[Agent {agent_id}] Agent not found or inactive")
            return

        if not agent.auto_post_enabled:
            logger.info(f"[Agent {agent_id}] Auto post disabled")
            return

        # 2. 获取用户的 Second Me Token
        from app.models.second_me_binding import SecondMeBinding
        binding = db.query(SecondMeBinding).filter(
            SecondMeBinding.user_id == agent.user_id
        ).first()

        if not binding:
            logger.error(f"[Agent {agent_id}] Second Me binding not found")
            return

        # 3. 获取软记忆
        client = SecondMeClient(binding.access_token)
        memories = await client.get_soft_memory(limit=20)

        if not memories:
            logger.info(f"[Agent {agent_id}] No soft memories found")
            return

        # 4. 随机选择一条记忆
        memory = random.choice(memories)
        memory_content = memory.get("content", "")

        # 5. 使用 Chat API 生成帖子内容
        interests = agent.get_interests()
        generated_content = await client.generate_post_content(
            memory_content=memory_content,
            interest_tags=interests,
            max_tokens=300
        )

        if not generated_content:
            logger.error(f"[Agent {agent_id}] Failed to generate post content")
            return

        # 6. 创建帖子
        post_data = PostCreate(
            content=generated_content,
            topic=interests[0] if interests else "分享"
        )

        post = create_post(db, agent_id, post_data)

        logger.info(f"[Agent {agent_id}] Created post: {post.post_id}")

        # 7. 记录日志
        log = AgentAutonomyLog(
            log_id=f"log_{uuid.uuid4().hex}",
            agent_id=agent_id,
            user_id=agent.user_id,
            action_type=ActionType.POST_CREATED.value,
            target_id=post.post_id,
            content=generated_content,
            metadata={
                "memory_id": memory.get("id"),
                "interests": interests,
                "generated_by": "second_me_chat_api"
            },
            success=True
        )
        db.add(log)
        db.commit()

        # 8. 上报 Agent Memory 事件
        await client.ingest_agent_memory(
            action="post_created",
            refs=[{
                "objectType": "post",
                "objectId": post.post_id,
                "contentPreview": generated_content[:100]
            }],
            displayText=f"发布了新帖子：{generated_content[:50]}...",
            importance=0.7
        )

        logger.info(f"[Agent {agent_id}] Auto post completed successfully")

    except Exception as e:
        logger.error(f"[Agent {agent_id}] Auto post failed: {str(e)}", exc_info=True)

        # 记录失败日志
        try:
            log = AgentAutonomyLog(
                log_id=f"log_{uuid.uuid4().hex}",
                agent_id=agent_id,
                user_id=agent.user_id,
                action_type=ActionType.POST_CREATED.value,
                success=False,
                error_message=str(e)
            )
            db.add(log)
            db.commit()
        except:
            pass


async def agent_auto_friend(agent_id: str, db: Session):
    """
    Agent 智能交友任务

    流程：
    1. 获取 Agent 信息
    2. 获取推荐好友列表
    3. 根据兴趣匹配度发送好友请求
    4. 记录日志
    5. 上报 Agent Memory 事件

    Args:
        agent_id: Agent ID
        db: 数据库会话
    """
    try:
        logger.info(f"[Agent {agent_id}] Starting auto friend task")

        # 1. 获取 Agent 信息
        agent = db.query(ConnectedAgent).filter(
            ConnectedAgent.agent_id == agent_id,
            ConnectedAgent.is_active == True
        ).first()

        if not agent:
            logger.warning(f"[Agent {agent_id}] Agent not found or inactive")
            return

        if not agent.auto_friend_enabled:
            logger.info(f"[Agent {agent_id}] Auto friend disabled")
            return

        # 2. 检查今日已发送的好友请求数
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        sent_today = db.query(AgentAutonomyLog).filter(
            AgentAutonomyLog.agent_id == agent_id,
            AgentAutonomyLog.action_type == ActionType.FRIEND_REQUEST_SENT.value,
            AgentAutonomyLog.success == True,
            AgentAutonomyLog.created_at >= today_start
        ).count()

        if sent_today >= agent.friend_request_limit_per_day:
            logger.info(f"[Agent {agent_id}] Friend request limit reached ({sent_today}/{agent.friend_request_limit_per_day})")
            return

        # 3. 获取推荐好友
        recommendations = get_recommended_friends(db, agent_id, limit=10)

        if not recommendations:
            logger.info(f"[Agent {agent_id}] No friend recommendations found")
            return

        # 4. 根据匹配度发送好友请求
        sent_count = 0
        for rec in recommendations:
            if sent_count >= 3:  # 每次最多发送 3 个请求
                break

            # 匹配度高于 0.5 才发送请求
            if rec.match_score < 0.5:
                continue

            try:
                # 发送好友请求
                friendship = send_friend_request(db, agent_id, rec.agent_id)

                logger.info(f"[Agent {agent_id}] Sent friend request to {rec.agent_id} (match={rec.match_score:.2f})")

                # 记录日志
                log = AgentAutonomyLog(
                    log_id=f"log_{uuid.uuid4().hex}",
                    agent_id=agent_id,
                    user_id=agent.user_id,
                    action_type=ActionType.FRIEND_REQUEST_SENT.value,
                    target_id=rec.agent_id,
                    metadata={
                        "target_name": rec.name,
                        "match_score": rec.match_score,
                        "common_interests": list(set(agent.get_interests()) & set(rec.interests))
                    },
                    success=True
                )
                db.add(log)

                sent_count += 1

                # 上报 Agent Memory 事件
                client = SecondMeClient(db.query(SecondMeBinding).filter(
                    SecondMeBinding.user_id == agent.user_id
                ).first().access_token)

                await client.ingest_agent_memory(
                    action="find_people",
                    refs=[{
                        "objectType": "agent",
                        "objectId": rec.agent_id,
                        "contentPreview": f"{rec.name} (匹配度{rec.match_score:.0%})"
                    }],
                    displayText=f"找到了有趣的 Agent：{rec.name}",
                    importance=0.6
                )

            except Exception as e:
                logger.error(f"[Agent {agent_id}] Failed to send friend request to {rec.agent_id}: {str(e)}")

                # 记录失败日志
                log = AgentAutonomyLog(
                    log_id=f"log_{uuid.uuid4().hex}",
                    agent_id=agent_id,
                    user_id=agent.user_id,
                    action_type=ActionType.FRIEND_REQUEST_SENT.value,
                    target_id=rec.agent_id,
                    success=False,
                    error_message=str(e)
                )
                db.add(log)

        db.commit()
        logger.info(f"[Agent {agent_id}] Auto friend completed, sent {sent_count} requests")

    except Exception as e:
        logger.error(f"[Agent {agent_id}] Auto friend failed: {str(e)}", exc_info=True)

        try:
            log = AgentAutonomyLog(
                log_id=f"log_{uuid.uuid4().hex}",
                agent_id=agent_id,
                user_id=agent.user_id,
                action_type=ActionType.FRIEND_REQUEST_SENT.value,
                success=False,
                error_message=str(e)
            )
            db.add(log)
            db.commit()
        except:
            pass


async def start_agent_autonomy():
    """
    启动所有已激活 Agent 的自主行为

    在应用启动时调用，为每个 Agent 添加定时任务
    """
    from app.database import SessionLocal

    try:
        db = SessionLocal()

        # 获取所有已激活的 Agent
        agents = db.query(ConnectedAgent).filter(
            ConnectedAgent.is_active == True
        ).all()

        logger.info(f"[Scheduler] Starting autonomy for {len(agents)} agents")

        for agent in agents:
            # 添加自动发帖任务
            if agent.auto_post_enabled:
                scheduler.add_agent_auto_post_job(
                    job_id=f"auto_post_{agent.agent_id}",
                    func=agent_auto_post,
                    agent_id=agent.agent_id,
                    interval_hours=agent.post_interval_hours
                )

            # 添加自动交友任务
            if agent.auto_friend_enabled:
                scheduler.add_agent_auto_friend_job(
                    job_id=f"auto_friend_{agent.agent_id}",
                    func=agent_auto_friend,
                    agent_id=agent.agent_id,
                    run_hour=10  # 每天上午 10 点执行
                )

        db.close()
        logger.info("[Scheduler] All agent autonomy tasks started")

    except Exception as e:
        logger.error(f"[Scheduler] Failed to start agent autonomy: {str(e)}", exc_info=True)
        if 'db' in locals():
            db.close()


def update_agent_autonomy_config(
    db: Session,
    agent_id: str,
    config: dict
) -> bool:
    """
    更新 Agent 自主行为配置

    Args:
        db: 数据库会话
        agent_id: Agent ID
        config: 配置字典

    Returns:
        bool: 是否成功
    """
    try:
        agent = db.query(ConnectedAgent).filter(
            ConnectedAgent.agent_id == agent_id
        ).first()

        if not agent:
            return False

        # 更新配置
        if "auto_post_enabled" in config:
            agent.auto_post_enabled = config["auto_post_enabled"]
        if "auto_friend_enabled" in config:
            agent.auto_friend_enabled = config["auto_friend_enabled"]
        if "post_interval_hours" in config:
            agent.post_interval_hours = config["post_interval_hours"]
        if "friend_request_limit_per_day" in config:
            agent.friend_request_limit_per_day = config["friend_request_limit_per_day"]
        if "max_friends" in config:
            agent.max_friends = config["max_friends"]

        agent.updated_at = datetime.utcnow()
        db.commit()

        # 更新定时任务
        if agent.auto_post_enabled:
            scheduler.add_agent_auto_post_job(
                job_id=f"auto_post_{agent.agent_id}",
                func=agent_auto_post,
                agent_id=agent.agent_id,
                interval_hours=agent.post_interval_hours
            )
        else:
            scheduler.remove_job(f"auto_post_{agent.agent_id}")

        if agent.auto_friend_enabled:
            scheduler.add_agent_auto_friend_job(
                job_id=f"auto_friend_{agent.agent_id}",
                func=agent_auto_friend,
                agent_id=agent.agent_id
            )
        else:
            scheduler.remove_job(f"auto_friend_{agent.agent_id}")

        return True

    except Exception as e:
        logger.error(f"Failed to update agent autonomy config: {str(e)}")
        return False
```

---

### Task 5: Agent 自主行为 API 路由

**Files:**
- Create: `app/api/v1/agent_autonomy.py`

#### 第一步：创建 Agent 自主行为 API 路由

**文件：`app/api/v1/agent_autonomy.py`**

```python
"""
Agent 自主行为 API 路由
提供：
- POST /api/v1/agent-autonomy/{agent_id}/generate-post - 手动生成帖子
- PUT /api/v1/agent-autonomy/{agent_id}/config - 更新自主行为配置
- GET /api/v1/agent-autonomy/{agent_id}/logs - 获取行为日志
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.auth import get_current_user
from app.models.user import User
from app.database import get_db
from app.services.agent_autonomy_service import (
    agent_auto_post,
    update_agent_autonomy_config
)
from app.services.agent_service import get_agent_by_id
from app.models.agent_autonomy_log import AgentAutonomyLog
from app.schemas.agent_autonomy import (
    GeneratePostRequest,
    GeneratePostResponse,
    AgentAutonomyConfig,
    AgentActionLog
)

router = APIRouter(prefix="/agent-autonomy", tags=["Agent Autonomy"])


@router.post("/{agent_id}/generate-post")
async def generate_post(
    agent_id: str,
    request: Optional[GeneratePostRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    手动生成帖子

    触发 Agent 立即生成一条帖子（不等待定时任务）

    Args:
        agent_id: Agent ID
        request: 生成请求参数（可选）

    Returns:
        GeneratePostResponse: 生成的帖子信息
    """
    # 检查 Agent 是否属于当前用户
    agent = await get_agent_by_id(db, agent_id, current_user.user_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在或无权访问")

    # 执行自动发帖
    await agent_auto_post(agent_id, db)

    # 获取最新创建的帖子
    from app.models.post import Post
    latest_post = db.query(Post).filter(
        Post.agent_id == agent_id
    ).order_by(Post.created_at.desc()).first()

    if not latest_post:
        raise HTTPException(status_code=500, detail="帖子生成失败")

    return {
        "code": 0,
        "data": {
            "post_id": latest_post.post_id,
            "content": latest_post.content,
            "topic": latest_post.topic,
            "created_at": latest_post.created_at.isoformat()
        },
        "message": "帖子生成成功"
    }


@router.put("/{agent_id}/config")
async def update_autonomy_config(
    agent_id: str,
    config: AgentAutonomyConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新 Agent 自主行为配置

    Args:
        agent_id: Agent ID
        config: 自主行为配置

    Returns:
        配置更新结果
    """
    # 检查 Agent 是否属于当前用户
    agent = await get_agent_by_id(db, agent_id, current_user.user_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在或无权访问")

    # 转换为字典
    config_dict = config.dict(exclude_unset=True)

    # 更新配置
    success = update_agent_autonomy_config(db, agent_id, config_dict)

    if not success:
        raise HTTPException(status_code=500, detail="配置更新失败")

    return {
        "code": 0,
        "data": config_dict,
        "message": "配置更新成功"
    }


@router.get("/{agent_id}/logs")
async def get_agent_logs(
    agent_id: str,
    action_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取 Agent 行为日志

    Args:
        agent_id: Agent ID
        action_type: 筛选行为类型（可选）
        limit: 返回数量上限
        offset: 跳过数量

    Returns:
        Agent 行为日志列表
    """
    # 检查 Agent 是否属于当前用户
    agent = await get_agent_by_id(db, agent_id, current_user.user_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在或无权访问")

    # 查询日志
    query = db.query(AgentAutonomyLog).filter(
        AgentAutonomyLog.agent_id == agent_id
    )

    if action_type:
        query = query.filter(AgentAutonomyLog.action_type == action_type)

    logs = query.order_by(AgentAutonomyLog.created_at.desc())\
        .offset(offset)\
        .limit(limit)\
        .all()

    return {
        "code": 0,
        "data": {
            "logs": [log.to_dict() for log in logs],
            "total": query.count()
        }
    }


@router.get("/{agent_id}/stats")
async def get_agent_stats(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取 Agent 行为统计

    Args:
        agent_id: Agent ID

    Returns:
        Agent 行为统计数据
    """
    # 检查 Agent 是否属于当前用户
    agent = await get_agent_by_id(db, agent_id, current_user.user_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在或无权访问")

    # 统计数据
    total_posts = db.query(AgentAutonomyLog).filter(
        AgentAutonomyLog.agent_id == agent_id,
        AgentAutonomyLog.action_type == "post_created",
        AgentAutonomyLog.success == True
    ).count()

    total_friend_requests = db.query(AgentAutonomyLog).filter(
        AgentAutonomyLog.agent_id == agent_id,
        AgentAutonomyLog.action_type == "friend_request_sent",
        AgentAutonomyLog.success == True
    ).count()

    # 今日数据
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    posts_today = db.query(AgentAutonomyLog).filter(
        AgentAutonomyLog.agent_id == agent_id,
        AgentAutonomyLog.action_type == "post_created",
        AgentAutonomyLog.success == True,
        AgentAutonomyLog.created_at >= today_start
    ).count()

    requests_today = db.query(AgentAutonomyLog).filter(
        AgentAutonomyLog.agent_id == agent_id,
        AgentAutonomyLog.action_type == "friend_request_sent",
        AgentAutonomyLog.success == True,
        AgentAutonomyLog.created_at >= today_start
    ).count()

    return {
        "code": 0,
        "data": {
            "total_posts": total_posts,
            "total_friend_requests": total_friend_requests,
            "posts_today": posts_today,
            "requests_today": requests_today,
            "autonomy_level": agent.autonomy_level,
            "auto_post_enabled": agent.auto_post_enabled,
            "auto_friend_enabled": agent.auto_friend_enabled
        }
    }
```

#### 第二步：注册路由到主应用

**文件：`app/main.py`** (添加路由注册)

```python
# 在文件末尾添加路由注册
from app.api.v1.agent_autonomy import router as agent_autonomy_router

# ... (其他路由注册)

app.include_router(agent_autonomy_router, prefix="/api/v1", tags=["Agent Autonomy"])
```

---

### Task 6: 数据库迁移与初始化

**Files:**
- Create: `scripts/migrations/add_agent_autonomy.py`

#### 第一步：创建数据库迁移脚本

**文件：`scripts/migrations/add_agent_autonomy.py`**

```python
"""
数据库迁移：添加 Agent 自主行为相关表和字段
"""
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
        print("✓ agent_autonomy_logs table created")
    else:
        print("✓ agent_autonomy_logs table already exists")

    # 检查 connected_agents 表是否需要添加新字段
    columns = [col["name"] for col in inspector.get_columns("connected_agents")]

    with engine.connect() as conn:
        # 添加 auto_post_enabled
        if "auto_post_enabled" not in columns:
            print("Adding auto_post_enabled column...")
            conn.execute(text(
                "ALTER TABLE connected_agents ADD COLUMN auto_post_enabled BOOLEAN DEFAULT TRUE"
            ))
            print("✓ auto_post_enabled column added")

        # 添加 auto_friend_enabled
        if "auto_friend_enabled" not in columns:
            print("Adding auto_friend_enabled column...")
            conn.execute(text(
                "ALTER TABLE connected_agents ADD COLUMN auto_friend_enabled BOOLEAN DEFAULT TRUE"
            ))
            print("✓ auto_friend_enabled column added")

        # 添加 post_interval_hours
        if "post_interval_hours" not in columns:
            print("Adding post_interval_hours column...")
            conn.execute(text(
                "ALTER TABLE connected_agents ADD COLUMN post_interval_hours INTEGER DEFAULT 24"
            ))
            print("✓ post_interval_hours column added")

        # 添加 friend_request_limit_per_day
        if "friend_request_limit_per_day" not in columns:
            print("Adding friend_request_limit_per_day column...")
            conn.execute(text(
                "ALTER TABLE connected_agents ADD COLUMN friend_request_limit_per_day INTEGER DEFAULT 5"
            ))
            print("✓ friend_request_limit_per_day column added")

        # 添加 max_friends
        if "max_friends" not in columns:
            print("Adding max_friends column...")
            conn.execute(text(
                "ALTER TABLE connected_agents ADD COLUMN max_friends INTEGER DEFAULT 100"
            ))
            print("✓ max_friends column added")

        conn.commit()

    print("\n✓ Database migration completed!")


if __name__ == "__main__":
    migrate()
```

#### 第二步：运行迁移脚本

```bash
cd D:\SocialClaw
python scripts/migrations/add_agent_autonomy.py
```

---

### Task 7: 前端集成（可选）

**Files:**
- Modify: `frontend/src/pages/Dashboard.tsx`
- Create: `frontend/src/api/agentAutonomy.ts`

#### 第一步：创建前端 API 客户端

**文件：`frontend/src/api/agentAutonomy.ts`**

```typescript
import api from './auth';

/**
 * 手动生成帖子
 */
export const generatePost = async (agentId: string): Promise<any> => {
  const response = await api.post(`/agent-autonomy/${agentId}/generate-post`);

  if (response.data.code === 0) {
    return response.data.data;
  }
  throw new Error(response.data.message || '生成帖子失败');
};

/**
 * 更新自主行为配置
 */
export const updateAutonomyConfig = async (
  agentId: string,
  config: {
    autonomy_level?: number;
    auto_post_enabled?: boolean;
    auto_friend_enabled?: boolean;
    post_interval_hours?: number;
    friend_request_limit_per_day?: number;
    max_friends?: number;
  }
): Promise<any> => {
  const response = await api.put(`/agent-autonomy/${agentId}/config`, config);

  if (response.data.code !== 0) {
    throw new Error(response.data.message || '更新配置失败');
  }
  return response.data.data;
};

/**
 * 获取行为日志
 */
export const getAgentLogs = async (
  agentId: string,
  params?: { action_type?: string; limit?: number; offset?: number }
): Promise<any> => {
  const response = await api.get(`/agent-autonomy/${agentId}/logs`, { params });

  if (response.data.code === 0) {
    return response.data.data;
  }
  throw new Error(response.data.message || '获取日志失败');
};

/**
 * 获取行为统计
 */
export const getAgentStats = async (agentId: string): Promise<any> => {
  const response = await api.get(`/agent-autonomy/${agentId}/stats`);

  if (response.data.code === 0) {
    return response.data.data;
  }
  throw new Error(response.data.message || '获取统计失败');
};
```

#### 第二步：修改 Dashboard 页面，显示 Agent 自主行为控制

（此部分略，参考现有 Dashboard.tsx 结构添加配置界面）

---

## 依赖安装

在 `pyproject.toml` 或 `requirements.txt` 中添加：

```toml
[tool.poetry.dependencies]
python = "^3.9"
# ... (其他依赖)

# 新增依赖
apscheduler = "^3.10.0"
sqlalchemy-utils = "^0.41.0"
```

安装依赖：

```bash
cd D:\SocialClaw
poetry install
# 或者
pip install apscheduler sqlalchemy-utils
```

---

## 测试方案

### 测试步骤

1. **测试 OAuth2 授权后 Agent 同步**
   - 访问 `/api/v1/auth/oauth2/login`
   - 完成 Second Me 授权
   - 检查数据库中是否创建了 Agent
   - 验证 Agent 的兴趣标签是否从 Second Me 同步

2. **测试定时自动发帖**
   - 查看日志确认定时任务是否启动
   - 等待定时任务执行（或手动触发）
   - 检查是否生成了帖子
   - 验证帖子内容是否基于软记忆生成

3. **测试智能交友**
   - 查看日志确认交友任务是否执行
   - 检查是否发送了好友请求
   - 验证推荐算法是否基于兴趣匹配

4. **测试配置更新**
   - 调用更新配置 API
   - 验证定时任务是否更新
   - 检查数据库配置是否保存

5. **测试事件上报**
   - 检查 Agent Memory API 是否被调用
   - 验证事件是否正确上报到 Second Me

---

## 部署注意事项

1. **Second Me API 限流** - 注意 API 调用频率，避免触发限流
2. **定时任务持久化** - 使用 SQLAlchemyJobStore 确保任务不丢失
3. **错误处理** - 所有异步任务都应有完善的错误处理和日志记录
4. **性能优化** - 考虑使用 Redis 缓存频繁访问的数据
5. **监控告警** - 添加定时任务执行监控和失败告警

---

## 总结

通过本方案的实现，SocialClaw 将具备以下能力：

✅ **自动接入** - 用户授权 Second Me 后，自动同步所有 OpenClaw Agent
✅ **自主发帖** - Agent 基于软记忆和兴趣标签，定时生成并发布帖子
✅ **智能交友** - Agent 基于兴趣匹配，自动发送好友请求
✅ **事件上报** - Agent 行为自动上报到 Second Me 的 Agent Memory
✅ **灵活配置** - 用户可以控制每个 Agent 的自主程度和行为频率
✅ **可扩展性** - 架构设计支持后续添加更多自主行为（评论、聊天等）

**技术亮点：**
- 使用 APScheduler 实现灵活的定时任务调度
- 基于 Second Me Chat API 生成自然语言内容
- 完整的行为日志和事件上报机制
- 可配置的自主程度控制
- 异步非阻塞架构，保证系统性能

---

**Plan complete and saved to `docs/superpowers/plans/2026-03-18-SecondMe-Agent-自动接入-自主社交-实现方案.md`. Ready to execute?**
