"""FDE Agent 系统相关数据：风险分析、尽调报告、决策建议、异常告警、运行记录、规则配置。"""
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Integer, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin


class RiskAssessment(Base, IDMixin, TimestampMixin):
    """风险分析 Agent 输出：采购单综合风险评估。"""

    __tablename__ = "risk_assessments"

    purchase_request_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("purchase_requests.id"), nullable=False, index=True
    )
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, comment="综合评分 0-100")
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, comment="low/medium/high")
    dimensions: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="各维度得分：amount/new_supplier/category/supplier_risk/frequency/budget"
    )
    analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="风险点说明")
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SupplierDueDiligence(Base, IDMixin, TimestampMixin):
    """供应商尽调 Agent 输出：背景报告。"""

    __tablename__ = "supplier_due_diligence"

    supplier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("suppliers.id"), nullable=False, index=True
    )
    report_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    business_info: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    news: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True, comment="舆情/新闻列表")
    risk_flags: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True, comment="风险信号")
    risk_level: Mapped[str] = mapped_column(String(20), default="low")
    report_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="尽调报告文本")


class AgentDecision(Base, IDMixin, TimestampMixin):
    """审批建议 Agent 输出。"""

    __tablename__ = "agent_decisions"

    purchase_request_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("purchase_requests.id"), nullable=False, index=True
    )
    decision: Mapped[str] = mapped_column(
        String(30), nullable=False, comment="approve/reject/supplement/human"
    )
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="置信度 0-1")
    reasons: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True, comment="决策理由列表")


class AnomalyAlert(Base, IDMixin, TimestampMixin):
    """异常检测 Agent 输出。"""

    __tablename__ = "anomaly_alerts"

    alert_type: Mapped[str] = mapped_column(
        String(30), nullable=False, comment="split_order/supplier_churn/amount_spike/..."
    )
    target_type: Mapped[str] = mapped_column(String(30), nullable=False, comment="supplier/department/material")
    target_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info", comment="info/warning/critical")
    status: Mapped[str] = mapped_column(String(20), default="open", comment="open/acknowledged/resolved")


class AgentRun(Base, IDMixin, TimestampMixin):
    """Agent 工作流运行记录（LangGraph checkpoint 关联）。"""

    __tablename__ = "agent_runs"

    purchase_request_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("purchase_requests.id"), nullable=True, index=True
    )
    workflow_name: Mapped[str] = mapped_column(String(50), default="procurement_review")
    status: Mapped[str] = mapped_column(String(20), default="running", comment="running/succeeded/failed/human_waiting")
    current_node: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    state_snapshot: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class RiskConfig(Base, IDMixin, TimestampMixin):
    """风险规则配置：管理员可调整各维度权重与阈值。"""

    __tablename__ = "risk_configs"

    dimension: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False, comment="amount/new_supplier/category/supplier_risk/frequency/budget"
    )
    weight: Mapped[float] = mapped_column(Float, default=0, comment="风险权重")
    threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="触发阈值")
    condition: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="触发条件描述")
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
