"""采购订单与订单明细（审批通过后生成，收货入库联动库存）。"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin


class PurchaseOrder(Base, IDMixin, TimestampMixin):
    """采购订单：审批通过的采购申请转化为正式订单，收货后联动库存。"""

    __tablename__ = "purchase_orders"

    order_no: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False, comment="订单号，如 PO20261003001"
    )
    purchase_request_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("purchase_requests.id"), unique=True, nullable=False, comment="来源采购申请"
    )
    supplier_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("suppliers.id"), nullable=True, comment="供应商"
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("departments.id"), nullable=True, comment="申请部门"
    )
    total_amount: Mapped[float] = mapped_column(Integer, nullable=False, comment="订单总金额（元）")
    status: Mapped[str] = mapped_column(
        String(20),
        default="confirmed",
        comment="confirmed/partial_received/received/closed/cancelled",
    )
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    items = relationship(
        "PurchaseOrderItem",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class PurchaseOrderItem(Base, IDMixin, TimestampMixin):
    """采购订单明细行。"""

    __tablename__ = "purchase_order_items"

    purchase_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("purchase_orders.id"), nullable=False, index=True
    )
    material_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("materials.id"), nullable=True
    )
    material_name: Mapped[str] = mapped_column(String(150), nullable=False, comment="物料名称（快照）")
    spec: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    quantity: Mapped[float] = mapped_column(nullable=False, comment="订购数量")
    unit_price: Mapped[Optional[float]] = mapped_column(Integer, nullable=True, comment="单价")
    amount: Mapped[float] = mapped_column(Integer, nullable=False, comment="行金额")
    received_quantity: Mapped[float] = mapped_column(Integer, default=0, comment="已收货数量")

    purchase_order = relationship("PurchaseOrder", back_populates="items")
