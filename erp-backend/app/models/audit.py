"""审计日志：操作记录、审批记录、Agent 决策记录统一审计。"""
from typing import Any, Optional

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin


class AuditLog(Base, IDMixin, TimestampMixin):
    """审计日志表。"""

    __tablename__ = "audit_logs"

    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="操作人（Agent 操作为空）"
    )
    actor_type: Mapped[str] = mapped_column(
        String(20), default="user", comment="user/agent/system"
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False, comment="操作动作")
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="对象类型：purchase_request/approval/... "
    )
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    detail: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True, comment="变更详情")
    ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
