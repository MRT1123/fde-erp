"""库存与库存流水。"""
from typing import Optional

from sqlalchemy import Integer, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin


class Inventory(Base, IDMixin, TimestampMixin):
    """库存快照。"""

    __tablename__ = "inventories"

    material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("materials.id"), nullable=False, index=True
    )
    warehouse: Mapped[str] = mapped_column(String(50), default="default", comment="仓库")
    quantity: Mapped[float] = mapped_column(default=0, comment="可用库存")
    reserved_quantity: Mapped[float] = mapped_column(default=0, comment="预留库存")
    safety_stock: Mapped[Optional[float]] = mapped_column(nullable=True, comment="安全库存（预警线）")


class StockMovement(Base, IDMixin, TimestampMixin):
    """库存变动流水。"""

    __tablename__ = "stock_movements"

    material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("materials.id"), nullable=False, index=True
    )
    movement_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="in/out/adjust"
    )
    quantity: Mapped[float] = mapped_column(nullable=False, comment="变动数量（正数）")
    reference_type: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True, comment="来源：purchase_order/adjustment 等"
    )
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    operator_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("employees.id"), nullable=True
    )
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
