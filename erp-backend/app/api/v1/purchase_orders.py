"""采购订单 API：订单列表/详情、审批后生成订单、收货入库、取消订单。"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import DbSession
from app.services import purchase_order_service

router = APIRouter()


class CreateFromRequestIn(BaseModel):
    remark: Optional[str] = None


class ReceiveItemIn(BaseModel):
    order_item_id: int
    quantity: float = Field(gt=0)


class ReceiveIn(BaseModel):
    warehouse: str = Field(min_length=1)
    items: list[ReceiveItemIn]
    remark: Optional[str] = None


class CancelIn(BaseModel):
    remark: Optional[str] = None


@router.get("")
async def list_orders(db: DbSession):
    return await purchase_order_service.list_orders(db)


@router.get("/eligible")
async def list_eligible_requests(db: DbSession):
    """可下单的采购申请：已审批通过且未生成订单。"""
    return await purchase_order_service.list_eligible_requests(db)


@router.get("/{order_id}")
async def order_detail(order_id: int, db: DbSession):
    return await purchase_order_service.get_order(db, order_id)


@router.post("/from-request/{request_id}", status_code=201)
async def create_from_request(request_id: int, db: DbSession, payload: CreateFromRequestIn | None = None):
    """由已审批通过的采购申请生成采购订单。"""
    return await purchase_order_service.create_from_request(db, request_id, payload.remark if payload else None)


@router.post("/{order_id}/receive", status_code=201)
async def receive_order(order_id: int, payload: ReceiveIn, db: DbSession):
    """收货入库：更新订单明细收货量、增加库存并记录流水。"""
    return await purchase_order_service.receive(
        db,
        order_id,
        warehouse=payload.warehouse,
        items=[{"order_item_id": i.order_item_id, "quantity": i.quantity} for i in payload.items],
        remark=payload.remark,
    )


@router.post("/{order_id}/cancel")
async def cancel_order(order_id: int, db: DbSession, payload: CancelIn | None = None):
    return await purchase_order_service.cancel(db, order_id)
