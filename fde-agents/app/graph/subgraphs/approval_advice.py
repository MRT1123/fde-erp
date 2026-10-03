"""子图：审批建议（综合风险分 + 尽调报告输出决策建议）。"""
from langgraph.graph import END, StateGraph

from app.agents.approval_advisor import ApprovalAdvisor, _normalize_supplier_report
from app.graph.state import SubgraphState

advisor = ApprovalAdvisor()


async def decide_node(state: SubgraphState):
    """结合风险分析与供应商尽调，输出审批建议。"""
    result = await advisor.decide(
        risk_score=state.get("risk_score", 0.0),
        risk_analysis=state.get("risk_analysis", ""),
        supplier_report=_normalize_supplier_report(state.get("supplier_report", {})),
    )
    return {
        "approval_decision": result["decision"],
        "decision_reasons": result["reasons"],
        "needs_human_review": result["decision"] == "human",
    }


def build_approval_advice_subgraph() -> StateGraph:
    """构建审批建议子图。"""
    g = StateGraph(SubgraphState)
    g.add_node("decide", decide_node)
    g.set_entry_point("decide")
    g.add_edge("decide", END)
    return g
