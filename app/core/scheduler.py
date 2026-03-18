from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from typing import Callable, Optional
import logging

from app.core.config import settings
from app.core.logger import logger


def _job_executed(event):
    """任务执行成功回调"""
    logger.info(f"[Scheduler] Task executed successfully: {event.job_id}")


def _job_error(event):
    """任务执行失败回调"""
    logger.error(f"[Scheduler] Task execution failed: {event.job_id}, exception: {event.exception}")


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

        # 添加事件监听器
        self.scheduler.add_listener(_job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(_job_error, EVENT_JOB_ERROR)

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