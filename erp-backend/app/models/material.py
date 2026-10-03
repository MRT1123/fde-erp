"""物料主数据。"""
from typing import Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin


class Material(Base, IDMixin, TimestampMixin):
    """物料：采购对象主数据。"""

    __tablename__ = "materials"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="物料编码")
    name: Mapped[str] = mapped_column(String(150), nullable=False, comment="物料名称")
    category: Mapped[str] = mapped_column(String(50), nullable=False, comment="品类（办公/IT/生产/服务等）")
    spec: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="规格型号")
    unit: Mapped[str] = mapped_column(String(20), default="件", comment="计量单位")
    default_price: Mapped[Optional[float]] = mapped_column(Integer, nullable=True, comment="参考单价")
    status: Mapped[str] = mapped_column(String(20), default="active", comment="active/disabled")
