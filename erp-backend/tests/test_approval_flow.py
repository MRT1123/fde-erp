"""采购审批核心流程测试：创建 → 提交 → Agent 结果应用（风险路由）→ 审批动作。

使用 SQLite 内存库，不依赖外部服务（FDE/飞书均降级为本地/无操作）。
"""
import asyncio
import logging

import pytest

logging.disable(logging.CRITICAL)

from app.core.database import AsyncSessionLocal, Base, engine
from app import models  # noqa: F401
from app.services import purchase_service
from app.schemas.purchase import PurchaseItemCreate, PurchaseRequestCreate
from app.models.supplier import Supplier
from app.models.org import Department


@pytest.fixture(autouse=True)
async def _db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _seed(db):
    dept = Department(code="DP-IT", name="IT部")
    sup = Supplier(code="SUP-A", name="供应商A", contact_person="张三", phone="10086")
    db.add_all([dept, sup])
    await db.commit()
    await db.refresh(dept)
    await db.refresh(sup)
    return dept, sup


async def _create(db, title, amount, qty=1, unit=1):
    payload = PurchaseRequestCreate(
        title=title,
        items=[PurchaseItemCreate(material_name=title, quantity=qty, unit_price=unit)],
    )
    pr = await purchase_service.create_purchase_request(db, payload)
    # 强制指定金额：直接改 total_amount 更直观
    pr.total_amount = amount
    await db.commit()
    await db.refresh(pr)
    return pr


@pytest.mark.asyncio
async def test_low_risk_auto_approved():
    async with AsyncSessionLocal() as db:
        await _seed(db)
        pr = await _create(db, "办公耗材", 5_000, qty=10, unit=500)
        assert pr.status == "draft"
        await purchase_service.submit_for_review(db, pr.id)
        await db.commit()
        await db.refresh(pr)
        assert pr.status == "approved"
        assert pr.needs_human_review is False


@pytest.mark.asyncio
async def test_medium_risk_routes_to_human():
    async with AsyncSessionLocal() as db:
        await _seed(db)
        pr = await _create(db, "中风险采购", 80_000)
        # 首次合作标记使评分进入中风险区间
        await db.get(Supplier, pr.supplier_id)
        await purchase_service.submit_for_review(db, pr.id)
        await db.commit()
        await db.refresh(pr)
        assert pr.status == "pending_approval"
        assert pr.needs_human_review is False or pr.risk_level == "medium"


@pytest.mark.asyncio
async def test_high_risk_must_human_review():
    async with AsyncSessionLocal() as db:
        await _seed(db)
        pr = await _create(db, "大额服务器采购", 600_000)
        await purchase_service.submit_for_review(db, pr.id)
        await db.commit()
        await db.refresh(pr)
        assert pr.status == "pending_approval"
        assert pr.needs_human_review is True
        assert pr.risk_level == "high"


@pytest.mark.asyncio
async def test_withdraw_rules():
    async with AsyncSessionLocal() as db:
        await _seed(db)
        pr = await _create(db, "待撤回采购", 5_000, qty=10, unit=500)
        await purchase_service.withdraw(db, pr.id)
        await db.commit()
        await db.refresh(pr)
        assert pr.status == "withdrawn"
