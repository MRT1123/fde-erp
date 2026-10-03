"""专业子图包：每个子图是一个独立的 LangGraph 工作流。"""
from app.graph.subgraphs.anomaly_detection import build_anomaly_detection_subgraph
from app.graph.subgraphs.approval_advice import build_approval_advice_subgraph
from app.graph.subgraphs.risk_analysis import build_risk_analysis_subgraph
from app.graph.subgraphs.supplier_diligence import build_supplier_diligence_subgraph

__all__ = [
    "build_risk_analysis_subgraph",
    "build_supplier_diligence_subgraph",
    "build_approval_advice_subgraph",
    "build_anomaly_detection_subgraph",
]
