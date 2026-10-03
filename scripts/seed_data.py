"""演示数据种子脚本：部门、员工、物料、供应商、风险规则。

用法：
    python scripts/seed_data.py
（需先启动 PostgreSQL 并应用迁移：alembic upgrade head）
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "erp-backend"))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.material import Material
from app.models.org import Department, Employee
from app.models.risk import RiskConfig
from app.models.supplier import Supplier


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        # 部门
        if (await db.execute(select(Department).limit(1))).scalar_one_or_none() is None:
            tech = Department(name="技术部", code="TECH", budget_limit=1_000_000)
            ops = Department(name="运营部", code="OPS", budget_limit=800_000)
            finance = Department(name="财务部", code="FIN", budget_limit=500_000)
            db.add_all([tech, ops, finance])
            await db.flush()

            db.add_all(
                [
                    Employee(employee_no="E001", name="张伟", role="admin", department_id=tech.id, approval_limit=1_000_000),
                    Employee(employee_no="E002", name="李娜", role="department_approver", department_id=ops.id, approval_limit=100_000),
                    Employee(employee_no="E003", name="王强", role="senior_approver", department_id=finance.id, approval_limit=500_000),
                    Employee(employee_no="E004", name="赵敏", role="applicant", department_id=tech.id),
                ]
            )

        # 物料
        if (await db.execute(select(Material).limit(1))).scalar_one_or_none() is None:
            db.add_all(
                [
                    Material(code="M-IT-001", name="笔记本电脑", category="IT", unit="台", default_price=6_000),
                    Material(code="M-OF-001", name="打印纸 A4", category="办公", unit="箱", default_price=120),
                    Material(code="M-IT-002", name="显示器 27寸", category="IT", unit="台", default_price=1_500),
                ]
            )

        # 供应商
        if (await db.execute(select(Supplier).limit(1))).scalar_one_or_none() is None:
            db.add_all(
                [
                    Supplier(code="SUP001", name="北京智云科技", qualification_status="verified", risk_level="low", credit_score=88),
                    Supplier(code="SUP002", name="上海新达贸易", qualification_status="pending", risk_level="medium", credit_score=62),
                ]
            )

        # 风险规则配置（方案 5.1 默认权重）
        if (await db.execute(select(RiskConfig).limit(1))).scalar_one_or_none() is None:
            defaults = [
                ("amount", 30, 50000, "单笔采购金额 ≥ 50,000 元", "大额采购需人工复核"),
                ("new_supplier", 25, None, "首次合作供应商", "无历史交易记录"),
                ("category", 20, None, "采购品类与部门历史不符", "偏离正常采购模式"),
                ("supplier_risk", 25, None, "尽调发现工商异常/舆情风险", "信用风险信号"),
                ("frequency", 15, None, "同一供应商短期多次采购", "可能拆分规避审批"),
                ("budget", 20, None, "采购金额超出部门预算", "预算控制失效"),
            ]
            for dim, weight, threshold, condition, desc in defaults:
                db.add(RiskConfig(dimension=dim, weight=weight, threshold=threshold,
                                  condition=condition, description=desc))

        await db.commit()
        print("✅ 种子数据写入完成：部门/员工/物料/供应商/风险规则")


if __name__ == "__main__":
    asyncio.run(seed())
