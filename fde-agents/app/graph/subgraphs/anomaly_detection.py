"""子图：异常检测（基于历史采购数据分析拆分订单等异常模式）。"""
from langgraph.graph import END, StateGraph

from app.agents.anomaly_detector import AnomalyDetector
from app.graph.state import SubgraphState

detector = AnomalyDetector()


async def detect_node(state: SubgraphState):
    """输入历史采购记录，输出异常告警列表。"""
    history = state.get("history", [])
    alerts = await detector.detect(history)
    return {"anomaly_alerts": alerts}


def build_anomaly_detection_subgraph() -> StateGraph:
    """构建异常检测子图。"""
    g = StateGraph(SubgraphState)
    g.add_node("detect", detect_node)
    g.set_entry_point("detect")
    g.add_edge("detect", END)
    return g
