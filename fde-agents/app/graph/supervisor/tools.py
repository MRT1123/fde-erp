"""子图工具：把四个专业子图封装成 LangChain Tool，供 Supervisor 意图识别后分发。"""
import json

from langchain_core.tools import tool

from app.graph.subgraphs.anomaly_detection import build_anomaly_detection_subgraph
from app.graph.subgraphs.approval_advice import build_approval_advice_subgraph
from app.graph.subgraphs.risk_analysis import build_risk_analysis_subgraph
from app.graph.subgraphs.supplier_diligence import build_supplier_diligence_subgraph

RISK_SUBGRAPH = build_risk_analysis_subgraph().compile()
DILIGENCE_SUBGRAPH = build_supplier_diligence_subgraph().compile()
ADVICE_SUBGRAPH = build_approval_advice_subgraph().compile()
ANOMALY_SUBGRAPH = build_anomaly_detection_subgraph().compile()


@tool
async def analyze_risk(request_json: str) -> str:
    """子 Agent：风险分析。输入参数 request_json 为采购单 JSON（含 title、total_amount、
    supplier_id、supplier_name、purpose、items 等）。输出综合风险评分、风险级别、
    各维度得分与风险点说明。"""
    pr = json.loads(request_json)
    result = await RISK_SUBGRAPH.ainvoke({"purchase_request": pr})
    return json.dumps(
        {k: result.get(k) for k in ("risk_score", "risk_level", "dimensions", "risk_analysis")},
        ensure_ascii=False,
    )


@tool
async def supplier_diligence(request_json: str) -> str:
    """子 Agent：供应商尽调。输入参数 request_json 为采购单 JSON（需含 supplier_id、
    supplier_name）。输出供应商舆情、风险信号列表与尽调报告。"""
    pr = json.loads(request_json)
    result = await DILIGENCE_SUBGRAPH.ainvoke({"purchase_request": pr})
    return json.dumps({"supplier_report": result.get("supplier_report", {})}, ensure_ascii=False)


@tool
async def approval_advice(context_json: str) -> str:
    """子 Agent：审批建议。输入参数 context_json 为 JSON，包含 risk_score、
    risk_analysis、supplier_report（可由前面子 Agent 的结果拼装）。输出审批决策建议
    （approve/reject/supplement/human）与理由。"""
    ctx = json.loads(context_json)
    result = await ADVICE_SUBGRAPH.ainvoke(ctx)
    return json.dumps(
        {k: result.get(k) for k in ("approval_decision", "decision_reasons", "needs_human_review")},
        ensure_ascii=False,
    )


@tool
async def detect_anomaly(history_json: str) -> str:
    """子 Agent：异常检测。输入参数 history_json 为历史采购记录数组 JSON
    （每条含 supplier_id、amount、created_at）。输出异常告警列表（拆分订单等）。"""
    history = json.loads(history_json) if history_json else []
    result = await ANOMALY_SUBGRAPH.ainvoke({"history": history})
    return json.dumps({"anomaly_alerts": result.get("anomaly_alerts", [])}, ensure_ascii=False)


SUB_AGENT_TOOLS = [analyze_risk, supplier_diligence, approval_advice, detect_anomaly]
