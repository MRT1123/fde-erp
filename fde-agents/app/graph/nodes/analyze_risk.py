"""节点：风险分析。"""
from typing import Any

from app.agents.risk_analyzer import RiskAnalyzer


async def analyze_risk(state: dict[str, Any]) -> dict[str, Any]:
    """综合评估采购单风险，输出 0-100 分与风险点说明。"""
    analyzer = RiskAnalyzer()
    result = await analyzer.analyze(state.get("purchase_request") or {})
    return {
        "risk_score": result["risk_score"],
        "risk_analysis": result["analysis"],
        "dimensions": result["dimensions"],
    }
