"""供应商 API。"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierOut, SupplierRiskReport, SupplierUpdate
from app.services import supplier_service

router = APIRouter()


@router.get("", response_model=list[SupplierOut])
async def list_suppliers(db: DbSession, page: int = 1, page_size: int = 20):
    result = await db.execute(select(Supplier).order_by(Supplier.id.desc()).offset((page - 1) * page_size).limit(page_size))
    return result.scalars().all()


@router.post("", response_model=SupplierOut, status_code=201)
async def create_supplier(payload: SupplierCreate, db: DbSession):
    return await supplier_service.create_supplier(db, payload)


@router.get("/{supplier_id}", response_model=SupplierOut)
async def get_supplier(supplier_id: int, db: DbSession):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail="供应商不存在")
    return obj


@router.put("/{supplier_id}", response_model=SupplierOut)
async def update_supplier(supplier_id: int, payload: SupplierUpdate, db: DbSession):
    obj = await db.get(Supplier, supplier_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="供应商不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/{supplier_id}/risk-report", response_model=SupplierRiskReport)
async def get_supplier_risk_report(supplier_id: int, db: DbSession):
    """供应商风险报告（FDE 尽调 Agent 生成）。"""
    return await supplier_service.get_risk_report(db, supplier_id)
