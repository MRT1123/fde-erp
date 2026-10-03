"""采购申请与采购明细。"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin


class PurchaseRequest(Base, IDMixin, TimestampMixin):
    """采购申请：审批链路的核心业务对象。"""

    __tablename__ = "purchase_requests"

    request_no: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False, comment="申请单号，如 PR20261001001"
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="采购标题")
    applicant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employees.id"), nullable=False, index=True, comment="申请人"
    )
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.id"), nullable=False, index=True, comment="申请部门"
    )
    supplier_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("suppliers.id"), nullable=True, comment="拟选供应商"
    )
    total_amount: Mapped[float] = mapped_column(Integer, nullable=False, comment="总金额（元）")
    currency: Mapped[str] = mapped_column(String(10), default="CNY")
    purpose: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="采购用途")
    status: Mapped[str] = mapped_column(
        String(30),
        default="draft",
        index=True,
        comment=(
            "draft/analyzing/pending_approval/approving/approved/"
            "rejected/withdrawn/escalated/callback_error/needs_manual_review"
        ),
    )
    risk_score: Mapped[Optional[float]] = mapped_column(Integer, nullable=True, comment="Agent 综合风险评分 0-100")
    risk_level: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="low/medium/high"
    )
    needs_human_review: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否需要人工审批（高风险路由）"
    )
    budget_status: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="ok/over_budget/unknown"
    )
    agent_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Agent 分析摘要")
    feishu_instance_code: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="飞书审批实例 code"
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    items = relationship(
        "PurchaseItem",
        back_populates="purchase_request",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class PurchaseItem(Base, IDMixin, TimestampMixin):
    """采购明细行。"""

    __tablename__ = "purchase_items"

    purchase_request_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("purchase_requests.id"), nullable=False, index=True
    )
    material_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("materials.id"), nullable=True
    )
    material_name: Mapped[str] = mapped_column(String(150), nullable=False, comment="物料名称（快照）")
    spec: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    quantity: Mapped[float] = mapped_column(nullable=False, comment="数量")
    unit_price: Mapped[Optional[float]] = mapped_column(Integer, nullable=True, comment="单价")
    amount: Mapped[float] = mapped_column(Integer, nullable=False, comment="行金额")
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    purchase_request = relationship("PurchaseRequest", back_populates="items")
