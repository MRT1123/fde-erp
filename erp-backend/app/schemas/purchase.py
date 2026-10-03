"""采购申请相关 Schemas。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PurchaseItemCreate(BaseModel):
    material_id: Optional[int] = None
    material_name: str = Field(min_length=1, max_length=150)
    spec: Optional[str] = None
    quantity: float = Field(gt=0)
    unit_price: Optional[float] = None
    remark: Optional[str] = None


class PurchaseItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    material_name: str
    spec: Optional[str]
    quantity: float
    unit_price: Optional[float]
    amount: float
    remark: Optional[str]


class PurchaseRequestCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    supplier_id: Optional[int] = None
    purpose: Optional[str] = None
    applicant_id: Optional[int] = None
    department_id: Optional[int] = None
    items: list[PurchaseItemCreate] = Field(min_length=1)


class PurchaseRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_no: str
    title: str
    applicant_id: int
    department_id: int
    supplier_id: Optional[int]
    total_amount: float
    currency: str
    status: str
    budget_status: Optional[str] = None
    risk_score: Optional[float]
    risk_level: Optional[str]
    needs_human_review: bool
    agent_summary: Optional[str]
    created_at: datetime
    submitted_at: Optional[datetime]


class PurchaseRequestDetail(PurchaseRequestOut):
    items: list[PurchaseItemOut] = []
