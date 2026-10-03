"""通知任务：飞书消息推送。"""
from app.celery_app import celery_app
from app.services.feishu_service import feishu_service


@celery_app.task(name="tasks.send_feishu_message")
def send_feishu_message(user_id: str, text: str) -> None:
    """发送飞书消息（骨架，接入 SDK 后启用）。"""
    return None
