"""FDE Agent 服务客户端：ERP 后端调用 agent-service 触发风险分析。"""
import httpx

from app.core.config import settings


async def trigger_risk_analysis(request_id: int, request_payload: dict) -> dict:
    """调用 agent-service 的 /analyze 接口，返回风险分析结果。"""
    url = f"{settings.AGENT_SERVICE_URL}/analyze"
    async with httpx.AsyncClient(timeout=settings.AGENT_SERVICE_TIMEOUT) as client:
        resp = await client.post(url, json={"request_id": request_id, "purchase_request": request_payload})
        resp.raise_for_status()
        return resp.json()


async def get_supplier_due_diligence(supplier_id: int, supplier_name: str) -> dict:
    """调用 agent-service 的 /due-diligence 接口。"""
    url = f"{settings.AGENT_SERVICE_URL}/due-diligence"
    async with httpx.AsyncClient(timeout=settings.AGENT_SERVICE_TIMEOUT) as client:
        resp = await client.post(url, json={"supplier_id": supplier_id, "supplier_name": supplier_name})
        resp.raise_for_status()
        return resp.json()
