"""供应商服务。"""
import datetime as dt

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.risk import SupplierDueDiligence
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierRiskReport


async def create_supplier(db: AsyncSession, payload: SupplierCreate) -> Supplier:
    code = f"SUP{dt.date.today().strftime('%Y%m%d')}{(await db.execute(select(Supplier.id))).scalars().all().__len__() + 1:03d}"
    obj = Supplier(**payload.model_dump(), code=code, first_cooperation=True)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def get_risk_report(db: AsyncSession, supplier_id: int) -> SupplierRiskReport:
    """读取最近一份供应商尽调报告；没有时返回占位。"""
    supplier = await db.get(Supplier, supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="供应商不存在")

    result = await db.execute(
        select(SupplierDueDiligence)
        .where(SupplierDueDiligence.supplier_id == supplier_id)
        .order_by(SupplierDueDiligence.id.desc())
        .limit(1)
    )
    dd = result.scalar_one_or_none()
    return SupplierRiskReport(
        supplier_id=supplier.id,
        supplier_name=supplier.name,
        risk_level=supplier.risk_level,
        report_date=dd.report_date.isoformat() if dd else dt.date.today().isoformat(),
        business_info=dd.business_info if dd else None,
        risk_flags=dd.risk_flags if dd else [],
        report_content=dd.report_content if dd else "尚未生成尽调报告",
    )
