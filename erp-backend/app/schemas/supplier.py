"""供应商相关 Schemas。"""
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class SupplierCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    tax_no: Optional[str] = None


class SupplierUpdate(BaseModel):
    """供应商更新：仅需传入要修改的字段。"""

    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    tax_no: Optional[str] = None
    qualification_status: Optional[str] = None
    risk_level: Optional[str] = None
    credit_score: Optional[int] = None
    first_cooperation: Optional[bool] = None
    remark: Optional[str] = None
    status: Optional[str] = None


class SupplierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    contact_person: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    qualification_status: str
    risk_level: str
    credit_score: Optional[int]
    first_cooperation: bool
    status: str


class SupplierRiskReport(BaseModel):
    supplier_id: int
    supplier_name: str
    risk_level: str
    report_date: str
    business_info: Optional[dict[str, Any]] = None
    risk_flags: list[Any] = []
    report_content: Optional[str] = None
