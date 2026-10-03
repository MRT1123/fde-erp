"""ERP ↔ FDE 真实联动验证：提交采购单 → 调用 FDE Agent 服务(/analyze) → 应用结果。

用法（需先启动 FDE 服务，如 python -m uvicorn app.main:app --port 8001）：
    $env:AGENT_SERVICE_URL="http://localhost:8001"
    $env:DATABASE_URL="sqlite+aiosqlite:///./_verify_linkage.db"
    python ..\scripts\verify_linkage.py
"""
import asyncio
import logging
import os
import traceback

logging.disable(logging.CRITICAL)

from app.core.database import AsyncSessionLocal, Base, engine
from app import models  # noqa: F401
from app.services import purchase_service
from app.schemas.purchase import PurchaseItemCreate, PurchaseRequestCreate
from app.models.supplier import Supplier
from app.models.org import Department


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        dept = Department(code="DP-IT", name="IT部")
        sup = Supplier(
            code="SUP-HW", name="华为云", contact_person="张三",
            phone="10086", first_cooperation=True,
        )
        db.add_all([dept, sup])
        await db.commit()
        await db.refresh(dept)
        await db.refresh(sup)

        pr = await purchase_service.create_purchase_request(db, PurchaseRequestCreate(
            title="采购服务器50台",
            supplier_id=sup.id,
            purpose="扩容机房",
            items=[
                PurchaseItemCreate(material_name="服务器", quantity=50, unit_price=12000),
            ],
        ))
        print("CREATED", pr.request_no, "status=", pr.status)
        await purchase_service.submit_for_review(db, pr.id)
        await db.commit()
        await db.refresh(pr)
        print(
            "AFTER SUBMIT status=", pr.status,
            "risk=", pr.risk_score, pr.risk_level,
            "human=", pr.needs_human_review,
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        traceback.print_exc()
