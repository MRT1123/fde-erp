"""库存 API：库存查询、出入库操作、流水。"""
import datetime as dt

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.inventory import Inventory, StockMovement
from app.schemas.inventory import InventoryOut, StockChangeIn, StockMovementOut

router = APIRouter()


async def _get_or_create_inventory(db: DbSession, material_id: int, warehouse: str) -> Inventory:
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


@router.get("", response_model=list[InventoryOut])
async def list_inventory(db: DbSession):
    result = await db.execute(select(Inventory).order_by(Inventory.id))
    return result.scalars().all()


@router.get("/movements", response_model=list[StockMovementOut])
async def list_movements(db: DbSession, page: int = 1, page_size: int = 50):
    result = await db.execute(
        select(StockMovement).order_by(StockMovement.id.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    return result.scalars().all()


@router.post("/changes", response_model=StockMovementOut, status_code=201)
async def change_stock(payload: StockChangeIn, db: DbSession):
    """库存变动：in 入库 / out 出库 / adjust 盘盈盘亏。"""
    if payload.quantity <= 0:
        raise HTTPException(status_code=422, detail="数量必须为正数")
    if payload.movement_type not in {"in", "out", "adjust"}:
        raise HTTPException(status_code=422, detail="movement_type 仅支持 in/out/adjust")

    inv = await _get_or_create_inventory(db, payload.material_id, payload.warehouse)
    if payload.movement_type == "in":
        inv.quantity += payload.quantity
    elif payload.movement_type == "out":
        if inv.quantity < payload.quantity:
            raise HTTPException(status_code=409, detail="库存不足")
        inv.quantity -= payload.quantity
    elif payload.movement_type == "adjust":
        new_qty = payload.quantity  # adjust 语义：quantity 直接作为调整后数量
        inv.quantity = new_qty

    inv.updated_at = dt.datetime.now(dt.timezone.utc)
    movement = StockMovement(
        material_id=payload.material_id,
        movement_type=payload.movement_type,
        quantity=payload.quantity,
        reference_type=payload.reference_type,
        reference_id=payload.reference_id,
        remark=payload.remark,
    )
    db.add(movement)
    await db.commit()
    await db.refresh(movement)
    return movement
