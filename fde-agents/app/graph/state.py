"""LangGraph 状态定义：Supervisor 主图 + 子图共享的业务字段。

架构说明（多 Agent 协作 / Supervisor 模式）：
- 主图（supervisor graph）：Supervisor Agent 负责「意图识别」，通过工具调用把任务
  分发给下面的专业子图，而不是单个 LLM 直接输出结论。
- 子图（subgraph）：风险分析、供应商尽调、审批建议、异常检测四个专业 Agent，
  每个子图内部也是一个独立的 LangGraph 工作流。
"""
from typing import Annotated, Any, TypedDict

from langgraph.graph import MessagesState


class ProcurementState(TypedDict, total=False):
    """ERP 传入的采购上下文（子图输入）。"""

    request_id: int
    purchase_request: dict[str, Any]   # 采购单：title/amount/supplier/items/...
    supplier: dict[str, Any]           # 供应商上下文（可选）


class SubgraphState(ProcurementState):
    """子图输入输出状态：子图从 ProcurementState 取输入，回写各自业务字段。"""

    history: list[dict[str, Any]]       # 历史采购记录（异常检测子图输入）
    risk_score: float
    risk_level: str
    risk_analysis: str
    dimensions: dict[str, float]
    supplier_report: dict[str, Any]
    approval_decision: str
    decision_reasons: list[str]
    needs_human_review: bool
    anomaly_alerts: list[dict[str, Any]]


class SupervisorState(MessagesState, total=False):
    """Supervisor 主图状态：继承 LangGraph MessagesState 便于多轮工具调用。"""

    # ERP 上下文
    request_id: int
    purchase_request: dict[str, Any]

    # 子图回写字段（finalize 节点从工具结果中聚合）
    risk_score: float
    risk_level: str
    risk_analysis: str
    dimensions: dict[str, float]
    supplier_report: dict[str, Any]
    approval_decision: str
    decision_reasons: list[str]
    needs_human_review: bool
    anomaly_alerts: list[dict[str, Any]]

    # 最终结构化结果（返回给 ERP）
    final_result: dict[str, Any]
    error: str | None


# 子图共享的输出字段（finalize 聚合时使用）
SUBGRAPH_OUTPUT_FIELDS = (
    "risk_score",
    "risk_level",
    "risk_analysis",
    "dimensions",
    "supplier_report",
    "approval_decision",
    "decision_reasons",
    "needs_human_review",
    "anomaly_alerts",
)
