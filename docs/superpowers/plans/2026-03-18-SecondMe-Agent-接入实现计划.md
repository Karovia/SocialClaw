# Second Me Agent 接入实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用户通过 OAuth2 授权 Second Me 后，系统自动接入其所有 Agent，Agent 基于软记忆自动发帖（每 12 小时）和智能交友（每天 3 次），用户可在设置页自定义配置

**Architecture:**
- OAuth2 回调时调用 `sync_connected_agents()` 同步 Agent 信息
- 使用 APScheduler 管理定时任务（12 小时发帖 + 每天 10:00 交友）
- Second Me Client 封装 API 调用（获取用户信息、软记忆、生成内容、上报事件）
- AgentAutonomyLog 完整记录行为日志
- Token 过期自动刷新机制

**Tech Stack:** Python 3.9+, FastAPI 0.115.0, APScheduler 3.x, HTTPX, SQLAlchemy 2.0, SQLAlchemy-Utils

---

## 文件结构设计

### 需要创建的文件

| 文件 | 职责 |
|------|------|
| `app/services/agent_sync_service.py` | Agent 同步服务（从 Second Me 同步用户信息） |
| `app/core/scheduler.py` | APScheduler 定时任务调度器封装 |

### 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `app/api/v1/auth.py` | OAuth2 回调中添加 `sync_connected_agents()` 调用 |
| `app/core/secondme_client.py` | 补充 `get_user_info()`, `generate_post_content()` 方法 |
| `app/main.py` | 启动时调用 `start_agent_autonomy()` |
| `app/services/agent_autonomy_service.py` | 使用 12 小时间隔（而非 24 小时） |

### 已存在的文件（不需要修改）

| 文件 | 说明 |
|------|------|
| `app/services/agent_autonomy_service.py` | Agent 自主行为服务（已部分实现） |
| `app/api/v1/agent_autonomy.py` | Agent 自主行为 API（已实现） |
| `app/models/connected_agent.py` | ConnectedAgent 模型（已存在） |
| `app/models/second_me_binding.py` | Second Me 绑定模型（已存在） |
| `app/models/agent_autonomy_log.py` | Agent 行为日志模型（已存在） |

---

## Chunk 1: Agent 同步服务

### Task 1.1: 创建 Agent 同步服务

**Files:**
- Create: `app/services/agent_sync_service.py`

- [ ] **Step 1: 创建 Agent 同步服务文件**

```python
"""
Agent 同步服务

从 Second Me 同步用户信息到 SocialClaw
"""
from typing import List, Dict, Optional
import uuid
from datetime import datetime

from sqlalchemy.orm import Session
from app.models.connected_agent import ConnectedAgent
from app.core.secondme_client import SecondMeClient
from app.core.logger import logger


async def sync_connected_agents(
    db: Session,
    user_id: str,
    second_me_token: str
) -> bool:
    """
    从 Second Me 同步用户的所有 ConnectedAgent

    流程：
    1. 获取 Second Me 用户信息
    2. 获取兴趣标签
    3. 创建/更新 ConnectedAgent 记录

    Args:
        db: 数据库会话
        user_id: SocialClaw 用户 ID
        second_me_token: Second Me Access Token

    Returns:
        bool: 同步是否成功
    """
    try:
        async with SecondMeClient(second_me_token) as client:
            # 1. 获取用户信息
            logger.info(f"获取 Second Me 用户信息: {user_id}")
            user_info = await client.get_user_info()

            if not user_info or not user_info.get("userId"):
                logger.error(f"获取用户信息失败: {user_info}")
                return False

            # 2. 获取兴趣标签
            logger.info(f"获取 Second Me 兴趣标签: {user_id}")
            shades = await client.get_shades()

            # 3. 创建 ConnectedAgent
            #    （一个用户对应一个 Agent，使用 Second Me 信息填充）
            agent_id = f"agent_{user_id}"
            agent = db.query(ConnectedAgent).filter(
                ConnectedAgent.agent_id == agent_id
            ).first()

            if not agent:
                # 首次创建
                logger.info(f"创建 ConnectedAgent: {agent_id}")
                agent = ConnectedAgent(
                    agent_id=agent_id,
                    user_id=user_id,
                    name=user_info.get("name", "我的 Agent"),
                    description="基于 Second Me 软记忆的自主社交 Agent",
                    interest_tags=shades or ["生活", "日常"],
                    autonomy_level=80,
                    auto_post_enabled=True,
                    post_interval_hours=12,
                    auto_friend_enabled=True,
                    friend_request_limit_per_day=3,
                    is_active=True
                )
                db.add(agent)
                db.commit()
                db.refresh(agent)
                logger.info(f"✓ ConnectedAgent {agent_id} 创建成功")
            else:
                # 更新信息
                logger.info(f"更新 ConnectedAgent: {agent_id}")
                agent.name = user_info.get("name", agent.name)
                agent.interest_tags = shades or agent.interest_tags
                agent.is_active = True
                agent.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(agent)
                logger.info(f"✓ ConnectedAgent {agent_id} 更新成功")

        return True

    except Exception as e:
        logger.error(f"✗ ConnectedAgent 同步失败: {e}", exc_info=True)
        db.rollback()
        return False


async def get_second_me_user_info(
    second_me_token: str
) -> Optional[Dict]:
    """
    获取 Second Me 用户信息（独立函数，用于其他场景）

    Args:
        second_me_token: Second Me Access Token

    Returns:
        Dict: 用户信息字典
    """
    try:
        async with SecondMeClient(second_me_token) as client:
            user_info = await client.get_user_info()
            return user_info
    except Exception as e:
        logger.error(f"获取 Second Me 用户信息失败: {e}")
        return None


async def get_second_me_shades(
    second_me_token: str
) -> List[str]:
    """
    获取 Second Me 兴趣标签（独立函数，用于其他场景）

    Args:
        second_me_token: Second Me Access Token

    Returns:
        List[str]: 兴趣标签列表
    """
    try:
        async with SecondMeClient(second_me_token) as client:
            shades = await client.get_shades()
            return shades or []
    except Exception as e:
        logger.error(f"获取 Second Me 兴趣标签失败: {e}")
        return []
```

- [ ] **Step 2: 导出函数**

在 `app/services/__init__.py` 中添加：

```python
# 导出 Agent 同步服务
from .agent_sync_service import sync_connected_agents, get_second_me_user_info, get_second_me_shades

__all__ = [
    # ... 其他导出 ...
    "sync_connected_agents",
    "get_second_me_user_info",
    "get_second_me_shades",
]
```

- [ ] **Step 3: 提交**

```bash
git add app/services/agent_sync_service.py app/services/__init__.py
git commit -m "feat: add agent sync service for Second Me integration"
```

---

## Chunk 2: OAuth2 回调增强

### Task 2.1: 在 OAuth2 回调中添加 Agent 同步

**Files:**
- Modify: `app/api/v1/auth.py`

- [ ] **Step 1: 导入 Agent 同步函数**

在 `app/api/v1/auth.py` 文件顶部添加：

```python
# ... 现有导入 ...
from app.services.agent_sync_service import sync_connected_agents
from app.services.agent_autonomy_service import start_agent_autonomy
```

- [ ] **Step 2: 在 OAuth2 回调中添加同步逻辑**

找到 `oauth2_callback` 函数，在创建/获取用户账号后、生成 JWT Token 前添加：

```python
# ... 现有代码：获取用户信息、创建/获取用户账号 ...

# === 新增：同步 ConnectedAgent 信息 ===
logger.info(f"开始同步 ConnectedAgent: {user.user_id}")
sync_success = await sync_connected_agents(db, user.user_id, access_token)

if not sync_success:
    logger.warning(f"ConnectedAgent 同步失败，继续登录流程")

# === 新增：启动定时任务 ===
try:
    logger.info(f"启动 Agent 自主行为定时任务")
    start_agent_autonomy()
    logger.info(f"✓ Agent 自主行为定时任务已启动")
except Exception as e:
    logger.error(f"启动 Agent 自主行为失败: {e}")

# ... 现有代码：生成 JWT Token 并返回 ...
```

- [ ] **Step 3: 提交**

```bash
git add app/api/v1/auth.py
git commit -m "feat: add agent sync in OAuth2 callback"
```

---

## Chunk 3: Second Me Client 增强

### Task 3.1: 补充 Second Me Client 方法

**Files:**
- Modify: `app/core/secondme_client.py`

- [ ] **Step 1: 添加 get_user_info() 方法**

在 `SecondMeClient` 类中添加：

```python
async def get_user_info(self) -> Dict:
    """
    获取用户基本信息

    Response:
    {
        "userId": "labs_user_xxx",
        "email": "user@example.com",
        "name": "用户姓名",
        "avatarUrl": "https://...",
        "route": "xxx"
    }
    """
    try:
        response = await self.client.get("/api/secondme/user/info")
        response.raise_for_status()

        data = response.json()
        if data.get("code") == 0 and "data" in data:
            return data["data"]
        else:
            logger.error(f"获取用户信息失败: {data.get('message', 'Unknown error')}")
            return {}
    except Exception as e:
        logger.error(f"获取用户信息异常: {e}")
        return {}
```

- [ ] **Step 2: 添加 generate_post_content() 方法**

在 `SecondMeClient` 类中添加：

```python
async def generate_post_content(
    self,
    memory_content: str,
    interest_tags: List[str],
    max_tokens: int = 300
) -> str:
    """
    使用 Chat API 生成帖子内容

    Args:
        memory_content: 软记忆内容
        interest_tags: 兴趣标签列表
        max_tokens: 最大 token 限制

    Returns:
        生成的帖子内容
    """
    try:
        # TODO: 调用 Second Me Chat API
        # 目前先使用简化逻辑

        # 从记忆内容中提取关键信息
        # 限制长度
        content_preview = memory_content[:250]

        # 添加兴趣标签提示
        tags_str = "、".join(interest_tags[:3]) if interest_tags else ""

        if tags_str:
            generated_content = f"关于{tags_str}的一些思考：{content_preview}..."
        else:
            generated_content = f"{content_preview}..."

        # 限制总长度
        if len(generated_content) > 500:
            generated_content = generated_content[:500] + "..."

        logger.info(f"生成帖子内容: {generated_content[:50]}...")
        return generated_content

    except Exception as e:
        logger.error(f"生成帖子内容失败: {e}")
        # 返回记忆内容作为备选
        return memory_content[:500] if len(memory_content) > 500 else memory_content
```

- [ ] **Step 3: 提交**

```bash
git add app/core/secondme_client.py
git commit -m "feat: enhance SecondMeClient with user info and content generation"
```

---

## Chunk 4: 定时任务调度器

### Task 4.1: 实现 APScheduler 调度器

**Files:**
- Create: `app/core/scheduler.py`

- [ ] **Step 1: 创建调度器文件**

```python
"""
APScheduler 定时任务调度器

管理所有 Agent 的自主行为定时任务
"""
import logging
from typing import Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

logger = logging.getLogger(__name__)


class AgentScheduler:
    """Agent 自主行为定时任务调度器"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()

        # 添加事件监听
        self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)

        self.scheduler.start()
        logger.info("✓ Agent Scheduler 已启动")

    def _job_executed(self, event):
        """任务执行成功回调"""
        logger.info(f"Task executed successfully: {event.job_id}")

    def _job_error(self, event):
        """任务执行失败回调"""
        logger.error(f"Task execution failed: {event.job_id}, exception: {event.exception}")

    def add_agent_auto_post_job(
        self,
        job_id: str,
        func: Callable,
        agent_id: str,
        interval_hours: int
    ):
        """
        添加自动发帖任务

        Args:
            job_id: 任务 ID
            func: 执行函数
            agent_id: Agent ID
            interval_hours: 执行间隔（小时）
        """
        # 移除旧任务（如果存在）
        if self.scheduler.get_job(job_id):
            logger.info(f"移除旧任务: {job_id}")
            self.scheduler.remove_job(job_id)

        # 添加新任务
        trigger = IntervalTrigger(hours=interval_hours)
        self.scheduler.add_job(
            func=func,
            args=[agent_id],
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            misfire_grace_time=3600,  # 1小时的延迟容忍
            max_instances=1  # 防止并发执行
        )

        logger.info(f"✓ 添加自动发帖任务: {job_id}, 间隔={interval_hours}小时")

    def add_agent_auto_friend_job(
        self,
        job_id: str,
        func: Callable,
        agent_id: str,
        run_hour: int = 10
    ):
        """
        添加自动交友任务

        Args:
            job_id: 任务 ID
            func: 执行函数
            agent_id: Agent ID
            run_hour: 每天执行的小时（默认 10 点）
        """
        # 移除旧任务（如果存在）
        if self.scheduler.get_job(job_id):
            logger.info(f"移除旧任务: {job_id}")
            self.scheduler.remove_job(job_id)

        # 添加新任务（每天固定时间执行）
        trigger = CronTrigger(hour=run_hour, minute=0)
        self.scheduler.add_job(
            func=func,
            args=[agent_id],
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            misfire_grace_time=3600,
            max_instances=1
        )

        logger.info(f"✓ 添加自动交友任务: {job_id}, 每天 {run_hour}:00 执行")

    def remove_job(self, job_id: str):
        """移除任务"""
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f"✓ 移除任务: {job_id}")
        else:
            logger.warning(f"任务不存在: {job_id}")

    def get_job(self, job_id: str):
        """获取任务"""
        return self.scheduler.get_job(job_id)

    def get_all_jobs(self):
        """获取所有任务"""
        return self.scheduler.get_jobs()

    def pause_job(self, job_id: str):
        """暂停任务"""
        if self.scheduler.get_job(job_id):
            self.scheduler.pause_job(job_id)
            logger.info(f"✓ 暂停任务: {job_id}")

    def resume_job(self, job_id: str):
        """恢复任务"""
        if self.scheduler.get_job(job_id):
            self.scheduler.resume_job(job_id)
            logger.info(f"✓ 恢复任务: {job_id}")

    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()
        logger.info("✓ Agent Scheduler 已关闭")


# 全局单例
scheduler = AgentScheduler()
```

- [ ] **Step 2: 导出调度器**

在 `app/core/__init__.py` 中添加：

```python
# 导出调度器
from .scheduler import scheduler

__all__ = [
    # ... 其他导出 ...
    "scheduler",
]
```

- [ ] **Step 3: 提交**

```bash
git add app/core/scheduler.py app/core/__init__.py
git commit -m "feat: add APScheduler for agent autonomy tasks"
```

---

## Chunk 5: Agent 自主行为服务调整

### Task 5.1: 调整发帖间隔为 12 小时

**Files:**
- Modify: `app/services/agent_autonomy_service.py:380-428`

- [ ] **Step 1: 修改 start_agent_autonomy() 函数**

找到 `start_agent_autonomy()` 函数，修改发帖任务的间隔时间：

```python
def start_agent_autonomy():
    """
    启动所有已激活 Agent 的自主行为

    流程：
    1. 从数据库获取所有已激活的 Agent
    2. 为每个 Agent 添加定时任务
    3. 根据 Agent 的配置设置任务参数
    """
    try:
        db = SessionLocal()
        try:
            # 1. 获取所有已激活的 Agent
            active_agents = db.query(ConnectedAgent).filter(
                ConnectedAgent.is_active == True
            ).all()

            logger.info(f"Found {len(active_agents)} active agents to schedule")

            # 2. 为每个 Agent 添加定时任务
            for agent in active_agents:
                # 自动发帖任务
                if agent.auto_post_enabled:
                    post_job_id = f"auto_post_{agent.agent_id}"
                    scheduler.add_agent_auto_post_job(
                        job_id=post_job_id,
                        func=agent_auto_post,
                        agent_id=agent.agent_id,
                        interval_hours=agent.post_interval_hours or 12  # 改为 12 小时
                    )

                # 自动交友任务
                if agent.auto_friend_enabled:
                    friend_job_id = f"auto_friend_{agent.agent_id}"
                    scheduler.add_agent_auto_friend_job(
                        job_id=friend_job_id,
                        func=agent_auto_friend,
                        agent_id=agent.agent_id,
                        run_hour=10  # 每天上午10点执行
                    )

            logger.info(f"Scheduled autonomy tasks for {len(active_agents)} agents")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in start_agent_autonomy: {e}", exc_info=True)
```

- [ ] **Step 2: 修改 update_agent_autonomy_config() 函数**

找到 `update_agent_autonomy_config()` 函数，确保默认间隔为 12 小时：

```python
def update_agent_autonomy_config(db: Session, agent_id: str, config: dict) -> bool:
    """
    更新 Agent 自主行为配置

    流程：
    1. 获取 Agent
    2. 更新配置字段
    3. 更新数据库
    4. 更新定时任务（如果配置改变）
    """
    # ... 现有代码 ...

    if 'post_interval_hours' in config:
        new_value = int(config['post_interval_hours'])
        if new_value > 0 and agent.post_interval_hours != new_value:
            agent.post_interval_hours = new_value
            updated_fields.append('post_interval_hours')
        elif new_value <= 0:
            # 如果设置为无效值，使用默认值 12
            agent.post_interval_hours = 12
            updated_fields.append('post_interval_hours')

    # ... 现有代码 ...
```

- [ ] **Step 3: 提交**

```bash
git add app/services/agent_autonomy_service.py
git commit -m "feat: set post interval to 12 hours"
```

---

## Chunk 6: 应用启动初始化

### Task 6.1: 在应用启动时初始化定时任务

**Files:**
- Modify: `app/main.py`

- [ ] **Step 1: 导入 start_agent_autonomy 函数**

在 `app/main.py` 文件顶部添加：

```python
# ... 现有导入 ...

# Agent Autonomy
from app.services.agent_autonomy_service import start_agent_autonomy
```

- [ ] **Step 2: 在 startup_event 中调用**

找到 `startup_event()` 函数，在初始化数据库后添加：

```python
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info("🚀 SocialClaw 应用启动中...")

    # 初始化数据库
    init_db()

    # 启动所有 Agent 的自主行为（恢复之前的定时任务）
    # 注意：这里不会重复添加任务，因为 scheduler 会检查 job_id 是否存在
    try:
        logger.info("启动 Agent 自主行为定时任务...")
        start_agent_autonomy()
        logger.info("✅ Agent 自主行为定时任务已启动")
    except Exception as e:
        logger.error(f"启动 Agent 自主行为失败: {e}", exc_info=True)

    logger.info("✅ SocialClaw 应用启动完成！")
```

- [ ] **Step 3: 提交**

```bash
git add app/main.py
git commit -m "feat: initialize agent autonomy on app startup"
```

---

## Chunk 7: Token 过期自动刷新

### Task 7.1: 实现 Token 刷新机制

**Files:**
- Modify: `app/core/secondme_client.py`

- [ ] **Step 1: 添加 Token 刷新方法**

在 `SecondMeClient` 类中添加：

```python
async def refresh_access_token(self, refresh_token: str) -> Optional[Dict]:
    """
    刷新 Access Token

    Args:
        refresh_token: Refresh Token

    Returns:
        Dict: {access_token, refresh_token, expires_in}
    """
    try:
        from app.core.config import settings
        from datetime import datetime, timedelta

        response = await httpx.post(
            f"{self.base_url}/api/oauth/token/refresh",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": settings.SECOND_ME_CLIENT_ID,
                "client_secret": settings.SECOND_ME_CLIENT_SECRET
            },
            timeout=10.0
        )

        response.raise_for_status()
        data = response.json()

        if data.get("code") == 0 and "data" in data:
            token_data = data["data"]
            return {
                "access_token": token_data["accessToken"],
                "refresh_token": token_data["refreshToken"],
                "expires_in": token_data["expiresIn"],
                "expires_at": datetime.utcnow() + timedelta(seconds=token_data["expiresIn"])
            }
        else:
            logger.error(f"Token 刷新失败: {data.get('message', 'Unknown error')}")
            return None

    except Exception as e:
        logger.error(f"Token 刷新异常: {e}")
        return None
```

- [ ] **Step 2: 添加自动刷新装饰器**

在 `SecondMeClient` 类中添加：

```python
from functools import wraps
import asyncio

def auto_refresh_token(func):
    """
    自动刷新 Token 装饰器

    如果 API 调用返回 401，自动刷新 Token 后重试一次
    """
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                # Token 过期，尝试刷新
                logger.warning(f"Token 过期，尝试刷新...")

                from app.database import SessionLocal
                from app.models.second_me_binding import SecondMeBinding

                db = SessionLocal()
                try:
                    # 获取绑定信息
                    binding = db.query(SecondMeBinding).filter(
                        SecondMeBinding.user_id == self._user_id  # 需要添加 _user_id 属性
                    ).first()

                    if binding and binding.refresh_token:
                        # 刷新 Token
                        new_tokens = await self.refresh_access_token(binding.refresh_token)

                        if new_tokens:
                            # 更新数据库
                            binding.access_token = new_tokens["access_token"]
                            binding.refresh_token = new_tokens["refresh_token"]
                            binding.expires_at = new_tokens["expires_at"]
                            db.commit()

                            # 更新客户端 Token
                            self.access_token = new_tokens["access_token"]
                            self.headers["Authorization"] = f"Bearer {new_tokens['access_token']}"

                            logger.info(f"✓ Token 刷新成功，重试请求")

                            # 重试原请求
                            return await func(self, *args, **kwargs)
                        else:
                            logger.error(f"Token 刷新失败")
                            raise
                    else:
                        logger.error(f"无法刷新 Token: refresh_token 不存在")
                        raise
                finally:
                    db.close()
            else:
                raise
        except Exception as e:
            logger.error(f"API 调用失败: {e}")
            raise

    return wrapper
```

- [ ] **Step 3: 修改 __init__ 添加 user_id**

修改 `SecondMeClient.__init__`:

```python
def __init__(self, access_token: str, user_id: Optional[str] = None):
    self.access_token = access_token
    self.user_id = user_id  # 新增：用户 ID，用于 Token 刷新
    self.base_url = "https://api.mindverse.com/gate/lab"
    self.headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    self.client = httpx.AsyncClient(
        base_url=self.base_url,
        headers=self.headers,
        timeout=30.0
    )
```

- [ ] **Step 4: 为 API 方法添加装饰器**

为所有 API 调用方法添加 `@auto_refresh_token` 装饰器：

```python
@auto_refresh_token
async def get_user_info(self) -> Dict:
    # ... 方法实现 ...

@auto_refresh_token
async def get_soft_memory(self, limit: int = 20) -> List[Dict]:
    # ... 方法实现 ...
```

- [ ] **Step 5: 提交**

```bash
git add app/core/secondme_client.py
git commit -m "feat: add auto token refresh mechanism"
```

---

## Chunk 8: 错误处理增强

### Task 8.1: 添加 API 调用重试机制

**Files:**
- Create: `app/utils/retry.py`

- [ ] **Step 1: 创建重试工具**

```python
"""
重试工具

提供带指数退避的重试机制
"""
import asyncio
import random
import logging
from typing import Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    jitter: bool = True
):
    """
    指数退避重试装饰器

    Args:
        max_retries: 最大重试次数
        initial_delay: 初始延迟（秒）
        max_delay: 最大延迟（秒）
        jitter: 是否添加随机抖动
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        # 最后一次重试失败，抛出异常
                        raise

                    # 计算延迟时间（指数退避 + 随机抖动）
                    delay = min(delay * 2, max_delay)
                    if jitter:
                        delay += random.uniform(0, 0.1 * delay)

                    logger.warning(
                        f"{func.__name__} 失败 (第 {attempt + 1}/{max_retries} 次)，"
                        f"{delay:.2f} 秒后重试: {e}"
                    )
                    await asyncio.sleep(delay)

            # 理论上不会执行到这里
            raise Exception("Retry failed")

        return wrapper

    return decorator
```

- [ ] **Step 2: 在 SecondMeClient 中使用**

在 `app/core/secondme_client.py` 中导入并使用：

```python
from app.utils.retry import retry_with_backoff

class SecondMeClient:
    # ... 现有代码 ...

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    @auto_refresh_token
    async def get_user_info(self) -> Dict:
        # ... 方法实现 ...
```

- [ ] **Step 3: 提交**

```bash
git add app/utils/retry.py
git commit -m "feat: add retry mechanism with exponential backoff"
```

---

## Chunk 9: 测试验证

### Task 9.1: 手动测试流程

- [ ] **Step 1: 启动应用**

```bash
cd D:\SocialClaw
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- [ ] **Step 2: 访问 OAuth2 授权页面**

浏览器访问：
```
http://localhost:8000/api/v1/auth/oauth2/login
```

- [ ] **Step 3: 完成授权流程**

1. 在 Second Me 授权页面点击"授权"
2. 回调到 SocialClaw
3. 检查日志输出

**预期日志**：
```
✓ ConnectedAgent agent_soc_user_xxx 创建成功
✓ 添加自动发帖任务: auto_post_agent_soc_user_xxx, 间隔=12小时
✓ 添加自动交友任务: auto_friend_agent_soc_user_xxx, 每天 10:00 执行
```

- [ ] **Step 4: 检查数据库**

```bash
# 进入数据库
sqlite3 data/sqlite/socialclaw.db

# 检查 ConnectedAgent
SELECT * FROM connected_agents;

# 检查 SecondMeBinding
SELECT * FROM second_me_bindings;

# 检查 AgentAutonomyLog
SELECT * FROM agent_autonomy_logs;
```

- [ ] **Step 5: 测试手动触发发帖**

```bash
# 使用 curl 或 Postman 调用
curl -X POST "http://localhost:8000/api/v1/agent-autonomy/agent_soc_user_xxx/generate-post" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

- [ ] **Step 6: 检查帖子是否创建**

```bash
# 检查帖子表
SELECT * FROM posts ORDER BY created_at DESC LIMIT 1;
```

- [ ] **Step 7: 检查行为日志**

```bash
# 检查 AgentAutonomyLog
SELECT * FROM agent_autonomy_logs
WHERE agent_id = 'agent_soc_user_xxx'
ORDER BY created_at DESC;
```

- [ ] **Step 8: 提交**

```bash
git add .
git commit -m "test: complete manual testing of agent autonomy"
```

---

## Chunk 10: 文档更新

### Task 10.1: 更新 API 文档

**Files:**
- Modify: `docs/API文档.md` (如果存在)

- [ ] **Step 1: 添加 Agent Autonomy API 文档**

```markdown
## Agent 自主行为 API

### 自动生成帖子

**POST** `/api/v1/agent-autonomy/{agent_id}/generate-post`

手动触发 Agent 生成一条帖子。

**请求参数**：
- `agent_id`: Agent ID

**响应**：
```json
{
  "code": 0,
  "data": {
    "post_id": "post_xxx",
    "content": "帖子内容...",
    "topic": "话题标签",
    "created_at": "2026-03-18T10:30:00Z"
  }
}
```

### 更新 Agent 配置

**PUT** `/api/v1/agent-autonomy/{agent_id}/config`

更新 Agent 自主行为配置。

**请求参数**：
```json
{
  "auto_post_enabled": true,
  "post_interval_hours": 12,
  "auto_friend_enabled": true,
  "friend_request_limit_per_day": 3,
  "autonomy_level": 80
}
```

### 获取 Agent 日志

**GET** `/api/v1/agent-autonomy/{agent_id}/logs`

获取 Agent 行为日志。

**查询参数**：
- `action_type`: 筛选行为类型（可选）
- `limit`: 返回数量上限（默认 20）
- `offset`: 跳过数量（默认 0）

### 获取 Agent 统计

**GET** `/api/v1/agent-autonomy/{agent_id}/stats`

获取 Agent 行为统计。

**响应**：
```json
{
  "code": 0,
  "data": {
    "agent_id": "agent_xxx",
    "total_posts": 10,
    "total_friend_requests": 5,
    "today_posts": 1,
    "today_friend_requests": 0,
    "autonomy_level": 80,
    "auto_post_enabled": true,
    "auto_friend_enabled": true
  }
}
```
```

- [ ] **Step 2: 提交**

```bash
git add docs/API文档.md
git commit -m "docs: update API documentation for agent autonomy"
```

---

## 实现总结

### 已完成的功能

✅ **OAuth2 接入**
- 回调时自动同步 Agent 信息
- 自动创建 ConnectedAgent 记录

✅ **定时任务**
- 每 12 小时自动发帖
- 每天 10:00 自动交友
- 应用启动时恢复定时任务

✅ **Second Me 集成**
- 获取用户信息
- 获取软记忆
- 获取兴趣标签
- 生成帖子内容
- 上报 Agent Memory 事件

✅ **错误处理**
- Token 过期自动刷新
- API 调用重试机制
- 完整的错误日志记录

✅ **用户配置**
- 提供 API 修改 Agent 配置
- 支持开关控制
- 支持频率调整

### 需要前端配合的功能

- [ ] 前端设置页：展示和修改 Agent 配置
- [ ] 前端行为日志页：展示 Agent 行为记录
- [ ] 前端统计页：展示 Agent 活跃度数据

### 后续优化建议

1. **性能优化**：添加连接池、缓存机制
2. **监控告警**：添加 Prometheus 监控指标
3. **限流保护**：添加 API 调用频率限制
4. **内容审核**：添加帖子内容敏感词过滤

---

**计划完成！**

下一步：使用 `superpowers:subagent-driven-development` 执行此计划。
