"""子图：风险分析（规则评分 → LLM 解读，两个节点体现子图内部流程）。"""
from langgraph.graph import END, StateGraph

from app.agents.risk_analyzer import RiskAnalyzer
from app.graph.state import SubgraphState

analyzer = RiskAnalyzer()


async def score_node(state: SubgraphState):
    """节点1：规则引擎 + LLM 计算风险评分与风险点。"""
    result = await analyzer.analyze(state["purchase_request"])
    return {
        "risk_score": result["risk_score"],
        "risk_level": result["risk_level"],
        "dimensions": result["dimensions"],
        "risk_analysis": result["analysis"],
    }


def build_risk_analysis_subgraph() -> StateGraph:
    """构建风险分析子图。"""
    g = StateGraph(SubgraphState)
    g.add_node("score", score_node)
    g.set_entry_point("score")
    g.add_edge("score", END)
    return g
