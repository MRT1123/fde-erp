"""超时检测与通知任务。"""
import asyncio

from app.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services.approval_service import escalate_timeout


@celery_app.task(name="tasks.check_approval_timeout")
def check_approval_timeout() -> dict:
    """周期任务：检查超时审批并升级。"""
    async def _run() -> dict:
        async with AsyncSessionLocal() as db:
            count = await escalate_timeout(db)
            return {"escalated": count}

    return asyncio.run(_run())
