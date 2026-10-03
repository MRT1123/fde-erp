"""节点：高风险路由到人工审批。"""
from typing import Any

from app.config import settings


def route_to_human(state: dict[str, Any]) -> dict[str, Any]:
    """标记需要人工审批，并生成转人工说明。

    实际推送飞书审批流由 ERP 后端完成（webhook 回调恢复流程）。
    """
    return {
        "needs_human_review": True,
        "approval_decision": "human",
    }


def route_by_risk_level(state: dict[str, Any]) -> str:
    """条件路由：risk_score >= 70 → human_review，否则 → auto_approve。"""
    risk_score = state.get("risk_score", 0.0)
    if risk_score >= settings.RISK_HIGH_THRESHOLD:
        return "human_review"
    return "auto_approve"
