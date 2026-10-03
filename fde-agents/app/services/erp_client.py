"""ERP 客户端：Agent 服务回读 ERP 数据。"""
import httpx

from app.config import settings


async def fetch_purchase_request(request_id: int) -> dict:
    """从 ERP 后端读取采购申请详情。"""
    url = f"{settings.ERP_API_URL}/api/v1/purchase-requests/{request_id}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


async def notify_analysis_result(request_id: int, result: dict) -> None:
    """通知 ERP 后端应用 Agent 分析结果。"""
    url = f"{settings.ERP_API_URL}/api/v1/internal/agent-result"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json={"request_id": request_id, "result": result})
        resp.raise_for_status()
