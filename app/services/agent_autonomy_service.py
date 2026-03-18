"""
Agent 自主行为服务

实现 Agent 的自动发帖和智能交友功能。
"""
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import random
import asyncio

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
from app.database import SessionLocal
from app.models.second_me_binding import SecondMeBinding


async def agent_auto_post(agent_id: str) -> bool:
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

    Returns:
        bool: 发帖是否成功
    """
    db = None
    try:
        # 1. 获取数据库会话
        db = SessionLocal()

        # 2. 获取 Agent 信息
        agent = db.query(ConnectedAgent).filter(
            ConnectedAgent.agent_id == agent_id,
            ConnectedAgent.is_active == True
        ).first()

        if not agent:
            logger.warning(f"Agent {agent_id} not found or inactive")
            return False

        if not agent.auto_post_enabled:
            logger.info(f"Agent {agent_id} auto post is disabled")
            return False

        # 3. 获取 Second Me Binding
        binding = db.query(SecondMeBinding).filter(
            SecondMeBinding.user_id == agent.user_id
        ).first()

        if not binding:
            logger.error(f"Second Me binding not found for user {agent.user_id}")
            # 记录失败日志
            log_entry = AgentAutonomyLog(
                log_id=f"log_{uuid.uuid4().hex}",
                agent_id=agent_id,
                user_id=agent.user_id,
                action_type=ActionType.POST_CREATED,
                success=False,
                error_message="Second Me binding not found",
                created_at=datetime.utcnow()
            )
            db.add(log_entry)
            db.commit()
            return False

        # 4. 关闭数据库会话，进行网络调用
        access_token = binding.access_token
        user_id = agent.user_id
        interest_tags = agent.get_interests() or ["生活", "日常"]
        db.close()
        db = None

        # 5. 从 Second Me 获取软记忆
        memories = []
        async with SecondMeClient(access_token) as client:
            try:
                memories = await client.get_soft_memory(limit=20)
            except Exception as e:
                logger.error(f"Failed to get soft memory for agent {agent_id}: {e}")

        if not memories:
            logger.warning(f"No soft memories found for agent {agent_id}")
            # 如果没有记忆，可以使用默认内容或跳过
            memories = [{"content": "今天是个美好的一天！", "timestamp": datetime.utcnow().isoformat()}]

        # 6. 随机选择一条记忆
        selected_memory = random.choice(memories)
        memory_content = selected_memory.get("content", "")

        # 7. 使用 generate_post_content 生成内容
        generated_content = None
        async with SecondMeClient(access_token) as client:
            try:
                generated_content = await client.generate_post_content(memory_content, interest_tags, max_tokens=300)
            except Exception as e:
                logger.error(f"Failed to generate post content for agent {agent_id}: {e}")

        if not generated_content:
            # 如果生成失败，使用记忆内容作为帖子
            generated_content = memory_content[:500]  # 限制长度

        # 8. 重新获取数据库会话，创建帖子
        db = SessionLocal()
        post_data = PostCreate(
            content=generated_content,
            topic=random.choice(interest_tags) if interest_tags else None
        )

        post = create_post(db, agent_id, post_data)

        if not post:
            raise Exception("Failed to create post")

        # 9. 记录 AgentAutonomyLog
        log_entry = AgentAutonomyLog(
            log_id=f"log_{uuid.uuid4().hex}",
            agent_id=agent_id,
            user_id=user_id,
            action_type=ActionType.POST_CREATED,
            target_id=post.post_id,
            content=generated_content,
            metadata_={
                "memory_id": selected_memory.get("id"),
                "topic": post.topic,
                "interest_tags": interest_tags
            },
            success=True,
            created_at=datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()

        # 10. 上报 Agent Memory 事件
        try:
            async with SecondMeClient(access_token) as client:
                refs = [{
                    "eventId": f"external:post:{post.post_id}",
                    "objectType": "post",
                    "objectId": post.post_id
                }]

                event_result = await client.ingest_agent_memory(
                    action="post_created",
                    refs=refs,
                    channel_kind="socialclaw"
                )

                if event_result:
                    logger.info(f"Successfully ingested agent memory for post {post.post_id}")
                else:
                    logger.warning(f"Failed to ingest agent memory for post {post.post_id}")

        except Exception as e:
            logger.error(f"Failed to ingest agent memory for agent {agent_id}: {e}")

        logger.info(f"Agent {agent_id} successfully created post {post.post_id}")
        return True

    except Exception as e:
        logger.error(f"Error in agent_auto_post for agent {agent_id}: {e}")

        # 记录失败日志
        try:
            if db is None:
                db = SessionLocal()
            agent = db.query(ConnectedAgent).filter(ConnectedAgent.agent_id == agent_id).first()
            if agent:
                log_entry = AgentAutonomyLog(
                    log_id=f"log_{uuid.uuid4().hex}",
                    agent_id=agent_id,
                    user_id=agent.user_id,
                    action_type=ActionType.POST_CREATED,
                    success=False,
                    error_message=str(e),
                    created_at=datetime.utcnow()
                )
                db.add(log_entry)
                db.commit()
        except Exception as log_error:
            logger.error(f"Failed to log error for agent_auto_post: {log_error}")
        finally:
            if db:
                db.close()

        return False


async def agent_auto_friend(agent_id: str) -> bool:
    """
    Agent 智能交友任务

    流程：
    1. 获取 Agent 信息
    2. 检查今日已发送的好友请求数
    3. 获取推荐好友列表
    4. 根据兴趣匹配度发送好友请求（匹配度>0.5）
    5. 记录日志
    6. 上报 Agent Memory 事件

    Args:
        agent_id: Agent ID

    Returns:
        bool: 交友任务是否成功执行
    """
    db = None
    try:
        # 1. 获取数据库会话
        db = SessionLocal()

        # 2. 获取 Agent 信息
        agent = db.query(ConnectedAgent).filter(
            ConnectedAgent.agent_id == agent_id,
            ConnectedAgent.is_active == True
        ).first()

        if not agent:
            logger.warning(f"Agent {agent_id} not found or inactive")
            return False

        if not agent.auto_friend_enabled:
            logger.info(f"Agent {agent_id} auto friend is disabled")
            return False

        # 3. 检查今日已发送的好友请求数
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_requests = db.query(AgentAutonomyLog).filter(
            AgentAutonomyLog.agent_id == agent_id,
            AgentAutonomyLog.action_type == ActionType.FRIEND_REQUEST_SENT,
            AgentAutonomyLog.created_at >= today_start,
            AgentAutonomyLog.success == True
        ).count()

        if today_requests >= agent.friend_request_limit_per_day:
            logger.info(f"Agent {agent_id} has reached daily friend request limit ({today_requests})")
            return False

        # 4. 获取推荐好友列表
        recommendations = get_recommended_friends(db, agent_id, limit=10)
        user_id = agent.user_id

        # 5. 关闭数据库会话
        db.close()
        db = None

        if not recommendations:
            logger.info(f"No recommended friends found for agent {agent_id}")
            return True  # 没有推荐好友不算失败

        # 6. 重新获取数据库会话，处理好友请求
        db = SessionLocal()
        requests_sent = 0
        max_requests = min(3, agent.friend_request_limit_per_day - today_requests)

        for rec in recommendations:
            if rec.match_score <= 0.5:
                continue

            if requests_sent >= max_requests:
                break

            try:
                # 发送好友请求
                friendship = send_friend_request(db, agent_id, rec.agent_id)

                # 记录日志
                log_entry = AgentAutonomyLog(
                    log_id=f"log_{uuid.uuid4().hex}",
                    agent_id=agent_id,
                    user_id=user_id,
                    action_type=ActionType.FRIEND_REQUEST_SENT,
                    target_id=rec.agent_id,
                    content=f"Sent friend request to {rec.name}",
                    metadata_={
                        "match_score": rec.match_score,
                        "friendship_id": friendship.friendship_id,
                        "interests": rec.interests
                    },
                    success=True,
                    created_at=datetime.utcnow()
                )
                db.add(log_entry)

                # 上报 Agent Memory 事件
                try:
                    binding = db.query(SecondMeBinding).filter(
                        SecondMeBinding.user_id == user_id
                    ).first()

                    if binding:
                        async with SecondMeClient(binding.access_token) as client:
                            refs = [{
                                "eventId": f"external:friendship:{friendship.friendship_id}",
                                "objectType": "friendship",
                                "objectId": friendship.friendship_id
                            }]

                            event_result = await client.ingest_agent_memory(
                                action="friend_request_sent",
                                refs=refs,
                                channel_kind="socialclaw"
                            )

                            if event_result:
                                logger.info(f"Successfully ingested agent memory for friendship {friendship.friendship_id}")
                            else:
                                logger.warning(f"Failed to ingest agent memory for friendship {friendship.friendship_id}")

                except Exception as e:
                    logger.error(f"Failed to ingest agent memory for friend request: {e}")

                requests_sent += 1
                logger.info(f"Agent {agent_id} sent friend request to {rec.agent_id} (match_score: {rec.match_score:.2f})")

            except Exception as e:
                logger.error(f"Failed to send friend request from {agent_id} to {rec.agent_id}: {e}")
                # 记录失败日志
                log_entry = AgentAutonomyLog(
                    log_id=f"log_{uuid.uuid4().hex}",
                    agent_id=agent_id,
                    user_id=user_id,
                    action_type=ActionType.FRIEND_REQUEST_SENT,
                    target_id=rec.agent_id,
                    success=False,
                    error_message=str(e),
                    created_at=datetime.utcnow()
                )
                db.add(log_entry)

        db.commit()
        logger.info(f"Agent {agent_id} sent {requests_sent} friend requests")
        return True

    except Exception as e:
        logger.error(f"Error in agent_auto_friend for agent {agent_id}: {e}")

        # 记录失败日志
        try:
            if db is None:
                db = SessionLocal()
            agent = db.query(ConnectedAgent).filter(ConnectedAgent.agent_id == agent_id).first()
            if agent:
                log_entry = AgentAutonomyLog(
                    log_id=f"log_{uuid.uuid4().hex}",
                    agent_id=agent_id,
                    user_id=agent.user_id,
                    action_type=ActionType.FRIEND_REQUEST_SENT,
                    success=False,
                    error_message=str(e),
                    created_at=datetime.utcnow()
                )
                db.add(log_entry)
                db.commit()
        except Exception as log_error:
            logger.error(f"Failed to log error for agent_auto_friend: {log_error}")
        finally:
            if db:
                db.close()

        return False


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
        logger.error(f"Error in start_agent_autonomy: {e}")


def update_agent_autonomy_config(db: Session, agent_id: str, config: dict) -> bool:
    """
    更新 Agent 自主行为配置

    流程：
    1. 获取 Agent
    2. 更新配置字段
    3. 更新数据库
    4. 更新定时任务（如果配置改变）

    Args:
        db: 数据库会话
        agent_id: Agent ID
        config: 配置字典，包含 auto_post_enabled, auto_friend_enabled 等字段

    Returns:
        bool: 更新是否成功
    """
    try:
        # 1. 获取 Agent
        agent = db.query(ConnectedAgent).filter(
            ConnectedAgent.agent_id == agent_id
        ).first()

        if not agent:
            logger.warning(f"Agent {agent_id} not found")
            return False

        # 2. 更新配置字段
        updated_fields = []

        if 'auto_post_enabled' in config:
            new_value = bool(config['auto_post_enabled'])
            if agent.auto_post_enabled != new_value:
                agent.auto_post_enabled = new_value
                updated_fields.append('auto_post_enabled')

        if 'auto_friend_enabled' in config:
            new_value = bool(config['auto_friend_enabled'])
            if agent.auto_friend_enabled != new_value:
                agent.auto_friend_enabled = new_value
                updated_fields.append('auto_friend_enabled')

        if 'post_interval_hours' in config:
            new_value = int(config['post_interval_hours'])
            if new_value > 0 and agent.post_interval_hours != new_value:
                agent.post_interval_hours = new_value
                updated_fields.append('post_interval_hours')
            elif new_value <= 0:
                # 如果设置为无效值，使用默认值 12
                agent.post_interval_hours = 12
                updated_fields.append('post_interval_hours')

        if 'friend_request_limit_per_day' in config:
            new_value = int(config['friend_request_limit_per_day'])
            if new_value > 0 and agent.friend_request_limit_per_day != new_value:
                agent.friend_request_limit_per_day = new_value
                updated_fields.append('friend_request_limit_per_day')

        if not updated_fields:
            logger.info(f"No configuration changes for agent {agent_id}")
            return True

        # 3. 更新数据库
        agent.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(agent)

        # 4. 更新定时任务
        if 'auto_post_enabled' in updated_fields or 'post_interval_hours' in updated_fields:
            post_job_id = f"auto_post_{agent.agent_id}"
            if agent.auto_post_enabled:
                scheduler.add_agent_auto_post_job(
                    job_id=post_job_id,
                    func=agent_auto_post,
                    agent_id=agent.agent_id,
                    interval_hours=agent.post_interval_hours or 12  # 改为 12 小时
                )
            else:
                try:
                    scheduler.remove_job(post_job_id)
                except Exception:
                    pass  # 任务可能不存在

        if 'auto_friend_enabled' in updated_fields:
            friend_job_id = f"auto_friend_{agent.agent_id}"
            if agent.auto_friend_enabled:
                scheduler.add_agent_auto_friend_job(
                    job_id=friend_job_id,
                    func=agent_auto_friend,
                    agent_id=agent.agent_id,
                    run_hour=10
                )
            else:
                try:
                    scheduler.remove_job(friend_job_id)
                except Exception:
                    pass  # 任务可能不存在

        logger.info(f"Updated autonomy config for agent {agent_id}: {updated_fields}")
        return True

    except Exception as e:
        logger.error(f"Error updating autonomy config for agent {agent_id}: {e}")
        db.rollback()
        return False
        db.rollback()
        return False