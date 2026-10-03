"""采购订单服务：审批通过后生成订单、收货入库（联动库存与流水）。"""
import datetime as dt
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import Inventory, StockMovement
from app.models.org import Department
from app.models.purchase import PurchaseRequest
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.models.supplier import Supplier

_RECEIVABLE_STATUS = ("confirmed", "partial_received")


async def _gen_order_no(db: AsyncSession) -> str:
    today = dt.date.today().strftime("%Y%m%d")
    prefix = f"PO{today}"
    rows = (
        await db.execute(select(PurchaseOrder.order_no).where(PurchaseOrder.order_no.like(f"{prefix}%")))
    ).scalars().all()
    max_seq = 0
    for no in rows:
        suffix = no[len(prefix):]
        if suffix.isdigit():
            max_seq = max(max_seq, int(suffix))
    seq = max_seq + 1
    return f"{prefix}{seq:03d}"


async def _get_or_create_inventory(db: AsyncSession, material_id: int, warehouse: str) -> Inventory:
    result = await db.execute(
        select(Inventory).where(
            Inventory.material_id == material_id,
            Inventory.warehouse == warehouse,
        )
    )
    inv = result.scalar_one_or_none()
    if inv is None:
        inv = Inventory(material_id=material_id, warehouse=warehouse, quantity=0, reserved_quantity=0)
        db.add(inv)
        await db.flush()
    return inv


async def create_from_request(db: AsyncSession, request_id: int, remark: Optional[str] = None) -> PurchaseOrder:
    """审批通过的采购申请 → 生成采购订单。"""
    purchase = await db.get(PurchaseRequest, request_id)
    if purchase is None:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    if purchase.status != "approved":
        raise HTTPException(status_code=409, detail=f"仅已审批通过的采购申请可生成订单（当前：{purchase.status}）")

    exists = (
        await db.execute(select(PurchaseOrder).where(PurchaseOrder.purchase_request_id == request_id))
    ).scalar_one_or_none()
    if exists is not None:
        raise HTTPException(status_code=409, detail=f"该采购申请已生成订单 {exists.order_no}，请勿重复下单")

    order = PurchaseOrder(
        order_no=await _gen_order_no(db),
        purchase_request_id=purchase.id,
        supplier_id=purchase.supplier_id,
        department_id=purchase.department_id,
        total_amount=purchase.total_amount,
        status="confirmed",
        remark=remark,
    )
    for item in purchase.items:
        order.items.append(
            PurchaseOrderItem(
                material_id=item.material_id,
                material_name=item.material_name,
                spec=item.spec,
                quantity=item.quantity,
                unit_price=item.unit_price,
                amount=item.amount,
                received_quantity=0,
            )
        )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


async def receive(
    db: AsyncSession,
    order_id: int,
    warehouse: str,
    items: list[dict],
    remark: Optional[str] = None,
    operator_id: Optional[int] = None,
) -> PurchaseOrder:
    """收货入库：按订单明细收货，更新库存与流水。

    items: [{"order_item_id": int, "quantity": float}]
    """
    if not warehouse:
        raise HTTPException(status_code=422, detail="仓库不能为空")
    if not items:
        raise HTTPException(status_code=422, detail="收货明细不能为空")

    order = await db.get(PurchaseOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    if order.status not in _RECEIVABLE_STATUS:
        raise HTTPException(status_code=409, detail=f"订单状态 {order.status} 不可收货")

    order_items = {it.id: it for it in order.items}
    total_qty = sum(it.quantity for it in order.items)
    newly_received = 0.0

    for line in items:
        item = order_items.get(line.get("order_item_id"))
        if item is None:
            raise HTTPException(status_code=404, detail=f"订单明细不存在：{line.get('order_item_id')}")
        qty = float(line.get("quantity") or 0)
        if qty <= 0:
            raise HTTPException(status_code=422, detail=f"明细 {item.material_name} 收货数量必须为正数")
        remaining = float(item.quantity) - float(item.received_quantity or 0)
        if qty > remaining:
            raise HTTPException(
                status_code=409,
                detail=f"明细 {item.material_name} 超量收货：剩余可收 {remaining}，本次 {qty}",
            )
        if item.material_id is None:
            raise HTTPException(status_code=422, detail=f"明细 {item.material_name} 未关联物料，无法入库")

        item.received_quantity = float(item.received_quantity or 0) + qty
        newly_received += qty
        # 库存增加 + 流水（reference_type=purchase_order 预留字段正式启用）
        inv = await _get_or_create_inventory(db, item.material_id, warehouse)
        inv.quantity = float(inv.quantity or 0) + qty
        db.add(
            StockMovement(
                material_id=item.material_id,
                movement_type="in",
                quantity=qty,
                reference_type="purchase_order",
                reference_id=order.id,
                operator_id=operator_id,
                remark=f"PO收货 {order.order_no} 仓库:{warehouse}{(' ' + remark) if remark else ''}",
            )
        )

    received_total = sum(float(it.received_quantity or 0) for it in order.items)
    order.status = "received" if received_total >= total_qty - 1e-6 else "partial_received"
    if remark:
        order.remark = remark
    await db.commit()
    await db.refresh(order)
    return order


async def cancel(db: AsyncSession, order_id: int) -> PurchaseOrder:
    """取消订单（未完全收货前可取消）。"""
    order = await db.get(PurchaseOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    if order.status == "received":
        raise HTTPException(status_code=409, detail="已收货完成的订单不可取消")
    order.status = "cancelled"
    await db.commit()
    await db.refresh(order)
    return order


async def _enrich(order: PurchaseOrder, db: AsyncSession) -> dict:
    request_no = ""
    supplier_name = ""
    department_name = ""
    if order.purchase_request_id:
        pr = await db.get(PurchaseRequest, order.purchase_request_id)
        request_no = pr.request_no if pr else ""
    if order.supplier_id:
        sup = await db.get(Supplier, order.supplier_id)
        supplier_name = sup.name if sup else ""
    if order.department_id:
        dept = await db.get(Department, order.department_id)
        department_name = dept.name if dept else ""
    return {
        "id": order.id,
        "order_no": order.order_no,
        "purchase_request_id": order.purchase_request_id,
        "request_no": request_no,
        "supplier_id": order.supplier_id,
        "supplier_name": supplier_name,
        "department_id": order.department_id,
        "department_name": department_name,
        "total_amount": order.total_amount,
        "status": order.status,
        "remark": order.remark,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "items": [
            {
                "id": it.id,
                "material_name": it.material_name,
                "spec": it.spec,
                "quantity": it.quantity,
                "unit_price": it.unit_price,
                "amount": it.amount,
                "received_quantity": it.received_quantity or 0,
            }
            for it in order.items
        ],
    }


async def list_eligible_requests(db: AsyncSession) -> list[dict]:
    """已审批通过且未生成采购订单的采购申请列表。"""
    result = await db.execute(
        select(PurchaseRequest).where(
            PurchaseRequest.status == "approved",
            ~PurchaseRequest.id.in_(select(PurchaseOrder.purchase_request_id)),
        ).order_by(PurchaseRequest.id.desc())
    )
    rows = []
    for pr in result.scalars().all():
        dept = await db.get(Department, pr.department_id) if pr.department_id else None
        sup = await db.get(Supplier, pr.supplier_id) if pr.supplier_id else None
        rows.append({
            "id": pr.id,
            "request_no": pr.request_no,
            "title": pr.title,
            "supplier_id": pr.supplier_id,
            "supplier_name": sup.name if sup else "",
            "department_id": pr.department_id,
            "department_name": dept.name if dept else "",
            "total_amount": pr.total_amount,
            "risk_level": pr.risk_level,
            "budget_status": pr.budget_status,
            "created_at": pr.created_at.isoformat() if pr.created_at else None,
        })
    return rows


async def list_orders(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(PurchaseOrder).order_by(PurchaseOrder.id.desc()))
    return [await _enrich(o, db) for o in result.scalars().all()]


async def get_order(db: AsyncSession, order_id: int) -> dict:
    order = await db.get(PurchaseOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    return await _enrich(order, db)
