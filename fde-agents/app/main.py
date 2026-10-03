"""FDE Agent 服务入口：对外暴露 /analyze、/due-diligence 等 HTTP 接口。"""
import json
from typing import Any

from fastapi import FastAPI, HTTPException
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.graph.graph import get_compiled_graph
from app.graph.supervisor.graph import SUPERVISOR_SYSTEM_PROMPT
from app.services.erp_client import fetch_purchase_request

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="FDE 智能风控 Agent：Supervisor 多 Agent 编排（意图识别分发子图）",
)


@app.get("/health", tags=["健康检查"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME}


@app.post("/analyze")
async def analyze(payload: dict[str, Any]):
    """执行采购风控工作流：Supervisor 意图识别 → 分发子图 → 返回结构化结果。

    入参：{request_id, purchase_request, history?}；
    返回：final_result（风险分/尽调/建议/异常告警）+ summary。
    """
    request_id = payload.get("request_id")
    purchase_request = payload.get("purchase_request") or {}
    history = payload.get("history") or []
    if not request_id:
        raise HTTPException(status_code=400, detail="request_id 必填")

    try:
        if not purchase_request:
            purchase_request = await fetch_purchase_request(request_id)
    except Exception:
        pass  # ERP 不可达时使用传入数据
    purchase_request["history"] = history

    graph = get_compiled_graph()
    messages = [
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
        HumanMessage(
            content=json.dumps(
                {"request_id": request_id, "purchase_request": purchase_request},
                ensure_ascii=False,
            )
        ),
    ]
    result = await graph.ainvoke(
        {
            "request_id": request_id,
            "purchase_request": purchase_request,
            "messages": messages,
        }
    )

    final = result.get("final_result") or {}
    summary = ""
    for msg in reversed(result.get("messages", [])):
        if getattr(msg, "type", "") == "ai" and not getattr(msg, "tool_calls", None):
            summary = str(msg.content)
            break
    return {"request_id": request_id, "final_result": final, "summary": summary}


@app.post("/due-diligence")
async def due_diligence(payload: dict[str, Any]):
    """单独执行供应商尽调（调试入口）。"""
    from app.agents.supplier_researcher import SupplierResearcher

    researcher = SupplierResearcher()
    report = await researcher.research(
        payload.get("supplier_id"),
        payload.get("supplier_name", ""),
    )
    return report


@app.post("/anomaly-check")
async def anomaly_check(payload: dict[str, Any]):
    """异常检测（调试入口）：输入历史采购记录。"""
    from app.agents.anomaly_detector import AnomalyDetector

    detector = AnomalyDetector()
    alerts = await detector.detect(payload.get("history") or [])
    return {"alerts": alerts}
