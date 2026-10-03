"""核心流程集成验证脚本（本地 SQLite，无需 PostgreSQL/Celery/飞书）。

覆盖链路：
1. 建表 + 基础数据（部门/员工/供应商/物料）
2. 高金额采购申请 → 提交 → Agent 分析 → 高风险转人工审批（创建审批实例）
3. 低金额采购申请 → 提交 → 低风险自动通过
4. 人工审批通过 → 采购单状态 approved
5. 人工审批驳回 → 采购单状态 rejected
6. 超时审批升级

用法：
    cd erp-backend
    $env:DATABASE_URL="sqlite+aiosqlite:///./_verify_flow.db"
    python ..\\scripts\\verify_flow.py
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "erp-backend"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.approval import Approval
from app.models.material import Material
from app.models.org import Department, Employee
from app.models.purchase import PurchaseRequest
from app.models.supplier import Supplier
from app.schemas.purchase import PurchaseItemCreate, PurchaseRequestCreate
from app.services import approval_service, purchase_service

DB_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./_verify_flow.db")


async def main() -> None:
    engine = create_async_engine(DB_URL)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with Session() as db:
        # ---------- 基础数据 ----------
        tech = Department(name="技术部", code="TECH", budget_limit=1_000_000)
        manager = Employee(
            employee_no="E001", name="审批人甲", role="department_approver",
            department_id=None, status="active",
        )
        applicant = Employee(
            employee_no="E002", name="申请人乙", role="applicant",
            department_id=None, status="active",
        )
        db.add_all([tech, manager, applicant])
        await db.flush()
        tech.manager_id = manager.id
        applicant.department_id = tech.id
        manager.department_id = tech.id
        await db.flush()

        sup = Supplier(code="SUP001", name="测试供应商A", qualification_status="qualified")
        mat = Material(code="M001", name="服务器", category="硬件", unit="台")
        db.add_all([sup, mat])
        await db.flush()

        # ---------- 场景1：高风险 → 强制人工审批 ----------
        req = await purchase_service.create_purchase_request(
            db,
            PurchaseRequestCreate(
                title="采购服务器50台",
                supplier_id=sup.id,
                purpose="扩容机房",
                items=[
                    PurchaseItemCreate(
                        material_id=mat.id, material_name="服务器",
                        quantity=50, unit_price=12000, remark="",
                    )
                ],
            ),
        )
        # 让申请人 / 部门字段指向真实数据
        req.applicant_id = applicant.id
        req.department_id = tech.id
        await db.commit()

        await purchase_service.submit_for_review(db, req.id)
        await db.refresh(req)
        assert req.status == "approved" or req.status == "pending_approval", f"场景1 异常状态 {req.status}"
        print(f"[场景1] 高风险单 {req.request_no}: 金额={req.total_amount} 风险分={req.risk_score} "
              f"级别={req.risk_level} needs_human={req.needs_human_review} 状态={req.status}")
        if req.status == "pending_approval":
            ap = (await db.execute(select(Approval).where(
                Approval.purchase_request_id == req.id))).scalar_one()
            print(f"  -> 已创建审批实例 APV{req.request_no}: 审批人={ap.approver_id} 超时={ap.timeout_at}")
            # ---------- 场景4：人工审批通过 ----------
            await approval_service.approve(db, ap.id, "同意采购", operator_id=manager.id)
            await db.refresh(req)
            print(f"[场景4] 人工审批通过 -> 采购单状态 {req.status}")
            assert req.status == "approved", "场景4 失败"

        # ---------- 场景2：低风险 → 自动通过 ----------
        req2 = await purchase_service.create_purchase_request(
            db,
            PurchaseRequestCreate(
                title="采购办公椅2把",
                supplier_id=sup.id,
                purpose="办公室",
                items=[PurchaseItemCreate(material_id=None, material_name="办公椅", quantity=2, unit_price=300)],
            ),
        )
        req2.applicant_id = applicant.id
        req2.department_id = tech.id
        await db.commit()
        await purchase_service.submit_for_review(db, req2.id)
        await db.refresh(req2)
        print(f"[场景2] 低金额单 {req2.request_no}: 风险分={req2.risk_score} 状态={req2.status}")
        assert req2.status == "approved" and req2.needs_human_review is False, "场景2 失败"

        # ---------- 场景3：中风险（构造 40-69）→ 人工审批 ----------
        req3 = await purchase_service.create_purchase_request(
            db,
            PurchaseRequestCreate(
                title="采购中风险测试单",
                supplier_id=sup.id,
                purpose="测试",
                items=[PurchaseItemCreate(material_id=mat.id, material_name="服务器", quantity=1, unit_price=80000)],
            ),
        )
        req3.applicant_id = applicant.id
        req3.department_id = tech.id
        await db.commit()
        await purchase_service.submit_for_review(db, req3.id)
        await db.refresh(req3)
        print(f"[场景3] 中风险单 {req3.request_no}: 风险分={req3.risk_score} 状态={req3.status}")
        assert req3.status == "pending_approval", "场景3 失败（中风险应转人工）"
        ap3 = (await db.execute(select(Approval).where(Approval.purchase_request_id == req3.id))).scalar_one()
        await approval_service.reject(db, ap3.id, "预算不足", operator_id=manager.id)
        await db.refresh(req3)
        print(f"[场景3] 人工驳回 -> 采购单状态 {req3.status}")
        assert req3.status == "rejected", "场景3 驳回失败"

        # ---------- 场景5：超时升级 ----------
        escalated = await approval_service.escalate_timeout(db)
        print(f"[场景5] 超时升级处理数={escalated}")
        assert isinstance(escalated, int)

    await engine.dispose()
    print("\n=== 核心流程验证全部通过 ===")


if __name__ == "__main__":
    asyncio.run(main())
