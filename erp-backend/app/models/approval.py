"""审批实例与审批操作日志。"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin


class Approval(Base, IDMixin, TimestampMixin):
    """审批实例：一次采购申请对应一到多个审批环节。"""

    __tablename__ = "approvals"

    purchase_request_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("purchase_requests.id"), nullable=False, index=True
    )
    approval_no: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, comment="审批编号")
    feishu_instance_code: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="飞书审批实例 code"
    )
    approver_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("employees.id"), nullable=True, comment="当前审批人"
    )
    status: Mapped[str] = mapped_column(
        String(30), default="pending", comment="pending/approving/approved/rejected/escalated"
    )
    decision: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="approved/rejected"
    )
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="审批意见")
    risk_score_snapshot: Mapped[Optional[float]] = mapped_column(
        Integer, nullable=True, comment="审批时的风险评分快照"
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    timeout_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="预计超时时间"
    )
    escalated_to: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("employees.id"), nullable=True, comment="超时升级到的审批人"
    )
    escalated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ApprovalAction(Base, IDMixin, TimestampMixin):
    """审批操作流水：通过/驳回/撤回/升级等。"""

    __tablename__ = "approval_actions"

    approval_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("approvals.id"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(
        String(30), nullable=False, comment="submit/accept/approve/reject/withdraw/escalate/transfer"
    )
    operator_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("employees.id"), nullable=True
    )
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    from_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    to_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
