"""采购申请 API：创建、查询、提交审批。"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession, get_current_user
from app.models.org import Employee
from app.models.purchase import PurchaseItem, PurchaseRequest
from app.schemas.purchase import PurchaseRequestCreate, PurchaseRequestDetail, PurchaseRequestOut
from app.services import purchase_service

router = APIRouter()


@router.post("", response_model=PurchaseRequestOut, status_code=status.HTTP_201_CREATED)
async def create_purchase_request(
    payload: PurchaseRequestCreate,
    db: DbSession,
    current_user: Annotated[Employee | None, Depends(get_current_user)] = None,
):
    """创建采购申请（草稿）。申请人优先取 payload.applicant_id，其次当前登录用户。"""
    return await purchase_service.create_purchase_request(db, payload, current_user)


@router.get("", response_model=list[PurchaseRequestOut])
async def list_purchase_requests(db: DbSession, page: int = 1, page_size: int = 20):
    """采购申请列表（分页）。"""
    stmt = (
        select(PurchaseRequest)
        .order_by(PurchaseRequest.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{request_id}", response_model=PurchaseRequestDetail)
async def get_purchase_request(request_id: int, db: DbSession):
    """采购申请详情（含明细）。"""
    stmt = (
        select(PurchaseRequest)
        .where(PurchaseRequest.id == request_id)
        .options(selectinload(PurchaseRequest.items))
    )
    result = await db.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    return obj


@router.post("/{request_id}/submit", response_model=PurchaseRequestOut)
async def submit_purchase_request(request_id: int, db: DbSession):
    """提交审批：触发 Agent 风险分析。"""
    return await purchase_service.submit_for_review(db, request_id)


@router.post("/{request_id}/withdraw", response_model=PurchaseRequestOut)
async def withdraw_purchase_request(request_id: int, db: DbSession):
    """撤回采购申请。"""
    return await purchase_service.withdraw(db, request_id)
