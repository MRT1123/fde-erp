"""审批相关 Schemas。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ApproveIn(BaseModel):
    comment: Optional[str] = Field(default=None, max_length=500)


class RejectIn(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class ApprovalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    purchase_request_id: int
    approval_no: str
    feishu_instance_code: Optional[str]
    approver_id: Optional[int]
    status: str
    decision: Optional[str]
    comment: Optional[str]
    risk_score_snapshot: Optional[float]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    timeout_at: Optional[datetime]


class ApprovalActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    operator_id: Optional[int]
    comment: Optional[str]
    from_status: Optional[str]
    to_status: Optional[str]
    created_at: datetime
