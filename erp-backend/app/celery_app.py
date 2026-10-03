"""Celery 应用：异步任务（Agent 分析、通知、超时检测）。"""
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "erp",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
)

celery_app.autodiscover_tasks(["app.tasks"])
