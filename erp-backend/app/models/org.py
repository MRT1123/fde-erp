"""组织架构：部门与员工。"""
from typing import Optional

from sqlalchemy import Integer, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin


class Department(Base, IDMixin, TimestampMixin):
    """部门：用于审批路由（按部门匹配审批人）与预算控制。"""

    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="部门名称")
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="部门编码")
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("departments.id"), nullable=True, comment="上级部门"
    )
    manager_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("employees.id"), nullable=True, comment="部门负责人"
    )
    budget_limit: Mapped[Optional[float]] = mapped_column(
        Integer, nullable=True, comment="年度预算上限（元）"
    )
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # 部门负责人
    manager = relationship("Employee", foreign_keys=[manager_id])
    # 部门成员
    employees = relationship("Employee", back_populates="department", foreign_keys="Employee.department_id")


class Employee(Base, IDMixin, TimestampMixin):
    """员工：兼任系统用户。"""

    __tablename__ = "employees"

    employee_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="工号")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="姓名")
    email: Mapped[Optional[str]] = mapped_column(String(120), unique=True, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    department_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("departments.id"), nullable=True, comment="所属部门"
    )
    role: Mapped[str] = mapped_column(
        String(30),
        default="applicant",
        comment="角色：applicant/department_approver/senior_approver/admin",
    )
    approval_limit: Mapped[Optional[float]] = mapped_column(
        Integer, nullable=True, comment="审批额度上限（元）"
    )
    feishu_user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="飞书用户ID")
    status: Mapped[str] = mapped_column(
        String(20), default="active", comment="状态：active/disabled/leave"
    )
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    department = relationship("Department", back_populates="employees", foreign_keys=[department_id])
