"""节点：审批建议。"""
from typing import Any

from app.agents.approval_advisor import ApprovalAdvisor


async def decide_approval(state: dict[str, Any]) -> dict[str, Any]:
    """综合风险分 + 尽调报告，给出「通过/驳回/补充材料/转人工」建议。"""
    advisor = ApprovalAdvisor()
    decision = await advisor.decide(
        risk_score=state.get("risk_score", 0.0),
        risk_analysis=state.get("risk_analysis", ""),
        supplier_report=state.get("supplier_report", {}),
    )
    return {
        "approval_decision": decision["decision"],
        "decision_reasons": decision["reasons"],
    }
