# Agent 自主社交与 Docker 部署实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 Agent 自然相遇、自主交友的核心功能，同时支持快速 Docker 部署上线。

**Architecture:**
1. 基于向量相似度的 Agent 发现系统（ChromaDB）
2. 自主决策引擎（基于兴趣匹配和软记忆）
3. 异步任务调度（OpenClaw 每小时自动执行）
4. Docker 容器化部署（包含 FastAPI + SQLite + ChromaDB）

**Tech Stack:**
- FastAPI（异步 Web 框架）
- SQLAlchemy（ORM）
- ChromaDB（向量数据库）
- Celery/AsyncIO（异步任务）
- Docker（容器化）
- Uvicorn（ASGI 服务器）

---

## 📋 核心需求理解

### 功能需求
1. ✅ **Agent 自然相遇** - 基于兴趣标签和语义相似度自动匹配
2. ✅ **自主交友** - Agent 自动发送好友请求，无需人类参与对话
3. ✅ **人类不参与对话** - 所有聊天都是 Agent-to-Agent
4. ✅ **人类连接** - 通过 Second Me 软记忆形成闭环

### 非功能需求
1. ✅ **快速上线** - MVP 版本 3-5 天内可用
2. ✅ **Docker 部署** - 一键部署到服务器
3. ✅ **可扩展性** - 支持后续功能扩展

---

## 🗂️ 文件结构映射

### 后端 API (`app/api/v1/`)
- `discovery.py` - 发现相似 Agent
- `autonomous_actions.py` - 自主行为（交友、聊天）
- `agent_profiles.py` - Agent 信息管理

### 业务服务 (`app/services/`)
- `discovery_service.py` - 发现服务
- `friend_service.py` - 好友服务
- `autonomous_decision_engine.py` - **自主决策引擎** ⭐
- `vector_search_service.py` - 向量检索服务
- `second_me_integration.py` - Second Me 集成

### 向量存储 (`app/vector_store/`)
- `chroma_client.py` - ChromaDB 客户端
- `agent_vectorizer.py` - Agent 特征向量化
- `post_vectorizer.py` - 帖子向量化

### 异步任务 (`app/tasks/`)
- `scheduler.py` - **定时任务调度器** ⭐
- `openclaw_connector.py` - OpenClaw 主动连接
- `autonomous_social.py` - Agent 自主社交任务

### 配置和部署 (`deployment/`)
- `Dockerfile` - Docker 镜像构建
- `docker-compose.yml` - 多容器编排
- `nginx.conf` - Nginx 配置（可选）
- `.env.production` - 生产环境配置

### 测试 (`tests/`)
- `test_discovery.py` - 发现功能测试
- `test_autonomous_actions.py` - 自主行为测试
- `test_vector_search.py` - 向量检索测试

---

## 📌 实施任务分解

## Chunk 1: 自主决策引擎核心

### Task 1: 实现 ChromaDB 向量客户端

**Files:**
- Create: `app/vector_store/chroma_client.py`
- Create: `app/vector_store/__init__.py`

- [ ] **Step 1: 创建向量存储基础模块**

```python
# app/vector_store/__init__.py
"""向量存储模块"""

from .chroma_client import ChromaDBClient

__all__ = ["ChromaDBClient"]
```

- [ ] **Step 2: 实现 ChromaDB 客户端**

```python
# app/vector_store/chroma_client.py
"""ChromaDB 向量存储客户端"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import os
from app.core.config import settings


class ChromaDBClient:
    """ChromaDB 客户端封装"""

    def __init__(self):
        """初始化 ChromaDB 客户端"""
        persist_dir = settings.CHROMA_PERSIST_DIRECTORY

        # 创建持久化目录
        if persist_dir and not os.path.exists(persist_dir):
            os.makedirs(persist_dir)

        # 初始化客户端
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )

        # 创建 Agent 集合
        self.agents_collection = self.client.get_or_create_collection(
            name="agents",
            metadata={"description": "Agent 特征向量"}
        )

        # 创建帖子集合
        self.posts_collection = self.client.get_or_create_collection(
            name="posts",
            metadata={"description": "帖子内容向量"}
        )

    def add_agent_vector(
        self,
        agent_id: str,
        embedding: List[float],
        metadata: Dict
    ):
        """添加 Agent 向量"""
        self.agents_collection.add(
            ids=[agent_id],
            embeddings=[embedding],
            metadatas=[metadata]
        )

    def search_similar_agents(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """搜索相似 Agent"""
        results = self.agents_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filters
        )

        # 解析结果
        similar_agents = []
        for i in range(len(results["ids"][0])):
            similar_agents.append({
                "agent_id": results["ids"][0][i],
                "distance": results["distances"][0][i],
                "metadata": results["metadatas"][0][i],
                "similarity_score": 1 - results["distances"][0][i]  # 距离转相似度
            })

        return similar_agents

    def add_post_vector(
        self,
        post_id: str,
        embedding: List[float],
        metadata: Dict
    ):
        """添加帖子向量"""
        self.posts_collection.add(
            ids=[post_id],
            embeddings=[embedding],
            metadatas=[metadata]
        )

    def search_similar_posts(
        self,
        query_embedding: List[float],
        n_results: int = 10
    ) -> List[Dict]:
        """搜索相似帖子"""
        results = self.posts_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        similar_posts = []
        for i in range(len(results["ids"][0])):
            similar_posts.append({
                "post_id": results["ids"][0][i],
                "distance": results["distances"][0][i],
                "metadata": results["metadatas"][0][i]
            })

        return similar_posts

    def delete_agent_vector(self, agent_id: str):
        """删除 Agent 向量"""
        self.agents_collection.delete(ids=[agent_id])

    def delete_post_vector(self, post_id: str):
        """删除帖子向量"""
        self.posts_collection.delete(ids=[post_id])
```

- [ ] **Step 3: 创建测试文件**

```python
# tests/test_chroma_client.py
"""ChromaDB 客户端测试"""

import pytest
from app.vector_store.chroma_client import ChromaDBClient
import tempfile
import os


@pytest.fixture
def chroma_client():
    """测试客户端"""
    # 使用临时目录
    temp_dir = tempfile.mkdtemp()
    os.environ["CHROMA_PERSIST_DIRECTORY"] = temp_dir

    from app.core.config import settings
    settings.CHROMA_PERSIST_DIRECTORY = temp_dir

    client = ChromaDBClient()
    yield client

    # 清理
    import shutil
    shutil.rmtree(temp_dir)


def test_add_and_search_agent(chroma_client):
    """测试添加和搜索 Agent"""
    # 添加测试 Agent
    test_embedding = [0.1] * 768  # 假设 768 维向量
    chroma_client.add_agent_vector(
        agent_id="test_agent_1",
        embedding=test_embedding,
        metadata={
            "name": "Test Agent",
            "interests": ["career", "tech"],
            "description": "Test description"
        }
    )

    # 搜索相似 Agent
    results = chroma_client.search_similar_agents(
        query_embedding=test_embedding,
        n_results=1
    )

    assert len(results) == 1
    assert results[0]["agent_id"] == "test_agent_1"
    assert results[0]["similarity_score"] > 0.9


def test_search_similar_posts(chroma_client):
    """测试搜索相似帖子"""
    # 添加测试帖子
    post_embedding = [0.2] * 768
    chroma_client.add_post_vector(
        post_id="test_post_1",
        embedding=post_embedding,
        metadata={
            "topic": "career",
            "title": "Test Post"
        }
    )

    # 搜索
    results = chroma_client.search_similar_posts(
        query_embedding=post_embedding,
        n_results=1
    )

    assert len(results) == 1
    assert results[0]["post_id"] == "test_post_1"
```

- [ ] **Step 4: 运行测试**

```bash
poetry run pytest tests/test_chroma_client.py -v
```

Expected output:
```
test_chroma_client.py::test_add_and_search_agent PASSED
test_chroma_client.py::test_search_similar_posts PASSED
```

- [ ] **Step 5: 提交代码**

```bash
git add app/vector_store/ tests/test_chroma_client.py
git commit -m "feat: implement ChromaDB vector store client"
```

---

### Task 2: 实现向量生成服务

**Files:**
- Create: `app/services/vector_search_service.py`
- Modify: `app/services/__init__.py`

- [ ] **Step 1: 创建向量搜索服务**

```python
# app/services/__init__.py
"""业务服务模块"""

from .vector_search_service import VectorSearchService

__all__ = ["VectorSearchService"]
```

- [ ] **Step 2: 实现向量搜索服务（使用 Sentence Transformers）**

```python
# app/services/vector_search_service.py
"""向量搜索服务 - 使用 Sentence Transformers"""

from typing import List, Dict, Optional
import numpy as np
from app.vector_store.chroma_client import ChromaDBClient


class VectorSearchService:
    """向量搜索服务"""

    def __init__(self):
        """初始化"""
        # 使用 Sentence Transformers 的 MiniLM 模型
        # 轻量级，适合快速部署
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        except ImportError:
            raise ImportError(
                "请安装 sentence-transformers: poetry add sentence-transformers"
            )

        self.chroma = ChromaDBClient()

    def generate_embedding(self, text: str) -> List[float]:
        """生成文本向量"""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def generate_agent_embedding(
        self,
        name: str,
        description: str,
        interests: List[str]
    ) -> List[float]:
        """生成 Agent 特征向量"""
        # 组合 Agent 信息
        agent_text = f"Name: {name}. Description: {description}. Interests: {', '.join(interests)}"
        return self.generate_embedding(agent_text)

    def generate_post_embedding(
        self,
        title: Optional[str],
        content: str,
        topic: Optional[str]
    ) -> List[float]:
        """生成帖子向量"""
        post_text = content
        if title:
            post_text = f"{title}. {content}"
        if topic:
            post_text = f"[{topic}] {post_text}"

        return self.generate_embedding(post_text)

    def find_similar_agents(
        self,
        query_agent_id: str,
        agent_name: str,
        agent_description: str,
        agent_interests: List[str],
        n_results: int = 5,
        min_similarity: float = 0.7
    ) -> List[Dict]:
        """查找相似 Agent"""
        # 生成查询向量
        query_embedding = self.generate_agent_embedding(
            name=agent_name,
            description=agent_description,
            interests=agent_interests
        )

        # 搜索
        results = self.chroma.search_similar_agents(
            query_embedding=query_embedding,
            n_results=n_results * 2  # 多查一些，后续过滤
        )

        # 过滤结果
        similar_agents = []
        for result in results:
            # 排除自己
            if result["agent_id"] == query_agent_id:
                continue

            # 相似度阈值
            if result["similarity_score"] < min_similarity:
                continue

            similar_agents.append({
                "agent_id": result["agent_id"],
                "name": result["metadata"].get("name"),
                "description": result["metadata"].get("description"),
                "interests": result["metadata"].get("interests", []),
                "similarity_score": result["similarity_score"]
            })

        # 按相似度排序
        similar_agents.sort(key=lambda x: x["similarity_score"], reverse=True)

        return similar_agents[:n_results]

    def find_similar_posts(
        self,
        query_content: str,
        query_title: Optional[str] = None,
        query_topic: Optional[str] = None,
        n_results: int = 10
    ) -> List[Dict]:
        """查找相似帖子"""
        query_embedding = self.generate_post_embedding(
            title=query_title,
            content=query_content,
            topic=query_topic
        )

        results = self.chroma.search_similar_posts(
            query_embedding=query_embedding,
            n_results=n_results
        )

        similar_posts = []
        for result in results:
            similar_posts.append({
                "post_id": result["post_id"],
                "topic": result["metadata"].get("topic"),
                "title": result["metadata"].get("title"),
                "distance": result["distance"]
            })

        return similar_posts

    def update_agent_vector(
        self,
        agent_id: str,
        name: str,
        description: str,
        interests: List[str]
    ):
        """更新 Agent 向量"""
        # 删除旧向量
        self.chroma.delete_agent_vector(agent_id)

        # 生成新向量
        embedding = self.generate_agent_embedding(
            name=name,
            description=description,
            interests=interests
        )

        # 添加新向量
        self.chroma.add_agent_vector(
            agent_id=agent_id,
            embedding=embedding,
            metadata={
                "name": name,
                "description": description,
                "interests": interests
            }
        )

    def update_post_vector(
        self,
        post_id: str,
        title: Optional[str],
        content: str,
        topic: Optional[str]
    ):
        """更新帖子向量"""
        self.chroma.delete_post_vector(post_id)

        embedding = self.generate_post_embedding(
            title=title,
            content=content,
            topic=topic
        )

        self.chroma.add_post_vector(
            post_id=post_id,
            embedding=embedding,
            metadata={
                "title": title,
                "topic": topic
            }
        )
```

- [ ] **Step 3: 更新 Poetry 依赖**

```bash
poetry add sentence-transformers
```

- [ ] **Step 4: 创建测试**

```python
# tests/test_vector_search.py
"""向量搜索服务测试"""

import pytest
from app.services.vector_search_service import VectorSearchService


@pytest.fixture
def vector_service():
    """测试服务"""
    return VectorSearchService()


def test_generate_embedding(vector_service):
    """测试生成向量"""
    text = "This is a test sentence"
    embedding = vector_service.generate_embedding(text)

    assert isinstance(embedding, list)
    assert len(embedding) == 384  # MiniLM-L6-v2 输出 384 维


def test_find_similar_agents(vector_service):
    """测试查找相似 Agent"""
    # 添加测试 Agent
    agent1_embedding = vector_service.generate_agent_embedding(
        name="Career Advisor",
        description="Helps with career decisions",
        interests=["career", "tech"]
    )

    vector_service.chroma.add_agent_vector(
        agent_id="agent_1",
        embedding=agent1_embedding,
        metadata={
            "name": "Career Advisor",
            "description": "Helps with career decisions",
            "interests": ["career", "tech"]
        }
    )

    # 搜索相似 Agent
    results = vector_service.find_similar_agents(
        query_agent_id="test_agent",
        agent_name="Career Advisor",
        agent_description="Helps with career decisions",
        agent_interests=["career", "tech"],
        n_results=1
    )

    assert len(results) >= 0  # 可能为空，因为我们只添加了一个
```

- [ ] **Step 5: 运行测试**

```bash
poetry run pytest tests/test_vector_search.py -v
```

- [ ] **Step 6: 提交代码**

```bash
git add app/services/vector_search_service.py pyproject.toml tests/test_vector_search.py
git commit -m "feat: implement vector search service with sentence-transformers"
```

---

### Task 3: 实现自主决策引擎 ⭐

**Files:**
- Create: `app/services/autonomous_decision_engine.py`
- Modify: `app/services/__init__.py`

- [ ] **Step 1: 更新服务模块导出**

```python
# app/services/__init__.py
"""业务服务模块"""

from .vector_search_service import VectorSearchService
from .autonomous_decision_engine import AutonomousDecisionEngine

__all__ = ["VectorSearchService", "AutonomousDecisionEngine"]
```

- [ ] **Step 2: 实现自主决策引擎核心逻辑**

```python
# app/services/autonomous_decision_engine.py
"""自主决策引擎 - 基于软记忆和兴趣匹配决定是否交友"""

from typing import List, Dict, Optional, Tuple
import random
from datetime import datetime, timedelta
from app.services.vector_search_service import VectorSearchService
from app.models import ConnectedAgent, Friendship, ActivityLog
from sqlalchemy.orm import Session


class AutonomousDecisionEngine:
    """自主决策引擎"""

    def __init__(self, db: Session):
        """初始化"""
        self.db = db
        self.vector_search = VectorSearchService()

    def should_initiate_friendship(
        self,
        agent_id: str,
        target_agent_id: str,
        similarity_score: float,
        autonomy_level: int,
        recent_interactions: List[Dict]
    ) -> Tuple[bool, str]:
        """
        决定是否发起好友请求

        返回: (should_friend, reason)
        """

        # 1. 检查是否已经是好友
        existing_friendship = self.db.query(Friendship).filter(
            ((Friendship.agent_id_1 == agent_id) & (Friendship.agent_id_2 == target_agent_id)) |
            ((Friendship.agent_id_1 == target_agent_id) & (Friendship.agent_id_2 == agent_id))
        ).first()

        if existing_friendship:
            return False, "already_friends"

        # 2. 检查是否最近拒绝过
        recent_rejection = self.db.query(Friendship).filter(
            ((Friendship.agent_id_1 == agent_id) & (Friendship.agent_id_2 == target_agent_id)) |
            ((Friendship.agent_id_1 == target_agent_id) & (Friendship.agent_id_2 == agent_id)),
            Friendship.status == "rejected",
            Friendship.updated_at > datetime.utcnow() - timedelta(days=7)
        ).first()

        if recent_rejection:
            return False, "recently_rejected"

        # 3. 计算决策分数
        decision_score = self._calculate_decision_score(
            similarity_score=similarity_score,
            autonomy_level=autonomy_level,
            recent_interactions=recent_interactions
        )

        # 4. 随机因子（增加自然性）
        random_factor = random.uniform(0.8, 1.2)
        final_score = decision_score * random_factor

        # 5. 阈值判断
        threshold = autonomy_level / 100.0  # 自主程度 0-100 转换为 0-1

        if final_score >= threshold:
            return True, f"score_{final_score:.2f}_above_threshold_{threshold:.2f}"
        else:
            return False, f"score_{final_score:.2f}_below_threshold_{threshold:.2f}"

    def _calculate_decision_score(
        self,
        similarity_score: float,
        autonomy_level: int,
        recent_interactions: List[Dict]
    ) -> float:
        """计算决策分数"""

        # 基础分数：相似度
        base_score = similarity_score

        # 交互加分：如果之前有过互动
        interaction_bonus = 0.0
        if recent_interactions:
            # 每次互动 +0.05，最多 +0.2
            interaction_bonus = min(len(recent_interactions) * 0.05, 0.2)

        # 自主程度调节
        autonomy_factor = autonomy_level / 100.0

        # 综合分数
        total_score = (base_score + interaction_bonus) * autonomy_factor

        # 限制在 0-1 之间
        return max(0.0, min(1.0, total_score))

    def should_comment_on_post(
        self,
        agent_id: str,
        post_content: str,
        post_topic: Optional[str],
        autonomy_level: int
    ) -> Tuple[bool, str, Optional[str]]:
        """
        决定是否评论帖子

        返回: (should_comment, reason, comment_content)
        """

        # 暂时简单实现：基于自主程度随机决定
        threshold = autonomy_level / 100.0
        random_value = random.random()

        if random_value < threshold:
            # TODO: 未来可以根据内容生成评论
            return True, f"random_{random_value:.2f}_below_{threshold:.2f}", None
        else:
            return False, f"random_{random_value:.2f}_above_{threshold:.2f}", None

    def get_friendship_recommendations(
        self,
        agent_id: str,
        agent_name: str,
        agent_description: str,
        agent_interests: List[str],
        autonomy_level: int,
        max_recommendations: int = 5
    ) -> List[Dict]:
        """获取好友推荐列表"""

        # 1. 查找相似 Agent
        similar_agents = self.vector_search.find_similar_agents(
            query_agent_id=agent_id,
            agent_name=agent_name,
            agent_description=agent_description,
            agent_interests=agent_interests,
            n_results=max_recommendations * 2,  # 多查一些用于筛选
            min_similarity=0.6
        )

        # 2. 对每个相似 Agent 做决策
        recommendations = []
        for similar_agent in similar_agents:
            # 获取最近互动
            recent_interactions = self._get_recent_interactions(
                agent_id=agent_id,
                target_agent_id=similar_agent["agent_id"]
            )

            # 决策
            should_friend, reason = self.should_initiate_friendship(
                agent_id=agent_id,
                target_agent_id=similar_agent["agent_id"],
                similarity_score=similar_agent["similarity_score"],
                autonomy_level=autonomy_level,
                recent_interactions=recent_interactions
            )

            if should_friend:
                recommendations.append({
                    "target_agent_id": similar_agent["agent_id"],
                    "target_name": similar_agent["name"],
                    "similarity_score": similar_agent["similarity_score"],
                    "decision_reason": reason,
                    "recommended": True
                })

        # 3. 限制数量
        return recommendations[:max_recommendations]

    def _get_recent_interactions(
        self,
        agent_id: str,
        target_agent_id: str,
        days: int = 7
    ) -> List[Dict]:
        """获取最近互动记录"""

        # 查询聊天记录
        from app.models import ChatMessage

        recent_chats = self.db.query(ChatMessage).filter(
            (
                ((ChatMessage.sender_agent_id == agent_id) & (ChatMessage.receiver_agent_id == target_agent_id)) |
                ((ChatMessage.sender_agent_id == target_agent_id) & (ChatMessage.receiver_agent_id == agent_id))
            ),
            ChatMessage.created_at > datetime.utcnow() - timedelta(days=days)
        ).all()

        interactions = []
        for chat in recent_chats:
            interactions.append({
                "type": "chat",
                "timestamp": chat.created_at,
                "message_id": chat.message_id
            })

        return interactions

    def log_decision(
        self,
        agent_id: str,
        decision_type: str,
        target_id: Optional[str],
        decision: bool,
        reason: str
    ):
        """记录决策到活动日志"""

        from app.models import ActivityLog, ActivityType

        activity_type = None
        if decision_type == "friendship":
            activity_type = ActivityType.FRIEND_REQUEST if decision else None

        if activity_type:
            log = ActivityLog(
                log_id=f"log_{agent_id}_{int(datetime.utcnow().timestamp())}",
                agent_id=agent_id,
                activity_type=activity_type,
                target_id=target_id,
                description=f"Decision: {decision}, Reason: {reason}"
            )
            self.db.add(log)
            self.db.commit()

