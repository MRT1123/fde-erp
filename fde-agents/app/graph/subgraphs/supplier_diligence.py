"""子图：供应商尽调（公开搜索 → 风险信号提取 → LLM 报告，三个节点）。"""
from langgraph.graph import END, StateGraph

from app.agents.supplier_researcher import SupplierResearcher
from app.graph.state import SubgraphState

researcher = SupplierResearcher()


async def research_node(state: SubgraphState):
    """搜索供应商舆情并生成尽调报告。"""
    supplier_id = state.get("purchase_request", {}).get("supplier_id")
    supplier_name = state.get("purchase_request", {}).get("supplier_name", "未知供应商")
    report = await researcher.research(supplier_id, supplier_name)
    return {"supplier_report": report}


def build_supplier_diligence_subgraph() -> StateGraph:
    """构建供应商尽调子图。"""
    g = StateGraph(SubgraphState)
    g.add_node("research", research_node)
    g.set_entry_point("research")
    g.add_edge("research", END)
    return g
