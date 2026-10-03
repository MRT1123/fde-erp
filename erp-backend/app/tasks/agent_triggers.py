"""Celery 任务：Agent 风险分析的异步派发（生产环境使用）。"""
from app.celery_app import celery_app
from app.services.agent_flow import run_risk_analysis


@celery_app.task(name="tasks.trigger_risk_analysis", bind=True, max_retries=3)
def trigger_risk_analysis(self, request_id: int) -> dict:
    """Celery 任务：调用 Agent 服务执行风险分析并应用结果。"""
    import asyncio

    return asyncio.run(run_risk_analysis(request_id))
