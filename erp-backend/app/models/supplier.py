"""供应商与供应商评级。"""
from datetime import date
from typing import Optional

from sqlalchemy import Integer, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin


class Supplier(Base, IDMixin, TimestampMixin):
    """供应商主数据。"""

    __tablename__ = "suppliers"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="供应商编码")
    name: Mapped[str] = mapped_column(String(150), nullable=False, comment="供应商名称")
    contact_person: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tax_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="统一社会信用代码")
    qualification_status: Mapped[str] = mapped_column(
        String(20), default="pending", comment="资质：pending/verified/rejected"
    )
    risk_level: Mapped[str] = mapped_column(
        String(20), default="low", comment="风险：low/medium/high"
    )
    credit_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="信用评分 0-100")
    first_cooperation: Mapped[bool] = mapped_column(default=False, comment="是否首次合作")
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", comment="active/disabled")


class SupplierRating(Base, IDMixin, TimestampMixin):
    """供应商评级记录。"""

    __tablename__ = "supplier_ratings"

    supplier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("suppliers.id"), nullable=False, index=True
    )
    rating_date: Mapped[date] = mapped_column(Date, nullable=False, comment="评级日期")
    score: Mapped[int] = mapped_column(Integer, nullable=False, comment="评级分数 0-100")
    level: Mapped[str] = mapped_column(String(20), nullable=False, comment="A/B/C/D")
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rated_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("employees.id"), nullable=True, comment="评级人"
    )
