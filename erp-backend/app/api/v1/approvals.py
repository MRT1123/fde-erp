"""审批 API：审批、驳回、撤回、查看操作流水。"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.approval import Approval, ApprovalAction
from app.models.purchase import PurchaseRequest
from app.schemas.approval import ApprovalActionOut, ApprovalOut, ApproveIn, RejectIn
from app.services import approval_service

router = APIRouter()


class ApprovalListItem(ApprovalOut):
    """审批列表项：附带采购申请摘要。"""
    model_config = ConfigDict(from_attributes=True)

    purchase_title: Optional[str] = None
    purchase_amount: float = 0


@router.get("", response_model=list[ApprovalListItem])
async def list_approvals(db: DbSession):
    """审批工作台列表（含采购标题与金额）。"""
    result = await db.execute(
        select(Approval, PurchaseRequest.title, PurchaseRequest.total_amount)
        .join(PurchaseRequest, PurchaseRequest.id == Approval.purchase_request_id)
        .order_by(Approval.id.desc())
    )
    rows = result.all()
    out: list[ApprovalListItem] = []
    for approval, title, amount in rows:
        item = ApprovalListItem.model_validate(approval)
        item.purchase_title = title
        item.purchase_amount = amount or 0
        out.append(item)
    return out


@router.get("/{approval_id}", response_model=ApprovalOut)
async def get_approval(approval_id: int, db: DbSession):
    result = await db.execute(select(Approval).where(Approval.id == approval_id))
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail="审批记录不存在")
    return obj


@router.post("/{approval_id}/approve", response_model=ApprovalOut)
async def approve(approval_id: int, payload: ApproveIn, db: DbSession):
    """审批通过。"""
    return await approval_service.approve(db, approval_id, payload.comment)


@router.post("/{approval_id}/reject", response_model=ApprovalOut)
async def reject(approval_id: int, payload: RejectIn, db: DbSession):
    """审批驳回。"""
    return await approval_service.reject(db, approval_id, payload.reason)


@router.get("/{approval_id}/actions", response_model=list[ApprovalActionOut])
async def list_actions(approval_id: int, db: DbSession):
    """审批操作流水。"""
    result = await db.execute(
        select(ApprovalAction).where(ApprovalAction.approval_id == approval_id).order_by(ApprovalAction.id)
    )
    return result.scalars().all()
