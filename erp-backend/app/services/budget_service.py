"""预算管控服务：部门预算占用统计与单笔采购预算校验。

预算口径：
- used（已用）：status=approved 的采购单金额合计（已批准待执行）
- pending（在途）：status in (analyzing, pending_approval, approving) 的金额合计（占用预算未最终确认）
- available（可用）= budget_limit - used - pending
- utilization = (used + pending) / budget_limit
- 单笔校验：budget_status = ok（扣减后仍 >=0）/ over_budget（扣减后 <0）/ unknown（部门未设上限）
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.org import Department
from app.models.purchase import PurchaseRequest

_OCCUPYING = ("analyzing", "pending_approval", "approving")


def _status_of(available_after: Optional[float], limit: Optional[float]) -> str:
    if limit is None:
        return "unknown"
    return "ok" if available_after >= 0 else "over_budget"


async def _dept_occupied(db: AsyncSession, department_id: int) -> tuple[float, float]:
    """返回 (used, pending)。"""
    result = await db.execute(
        select(PurchaseRequest.total_amount, PurchaseRequest.status).where(
            PurchaseRequest.department_id == department_id,
            PurchaseRequest.status.in_(("approved", *_OCCUPYING)),
        )
    )
    used, pending = 0.0, 0.0
    for amount, status in result.all():
        if status == "approved":
            used += float(amount or 0)
        else:
            pending += float(amount or 0)
    return used, pending


async def get_department_budget(db: AsyncSession, department: Department) -> dict:
    """部门预算总览（单部门）。"""
    limit = department.budget_limit
    used, pending = await _dept_occupied(db, department.id)
    available = None if limit is None else max(0.0, float(limit) - used - pending)
    utilization = None if not limit else round((used + pending) / float(limit) * 100, 1)
    status = "unknown" if limit is None else ("over_budget" if available == 0 and (used + pending) > float(limit) else "ok")
    # 可用不足 0 时同样视为超预算（可用=max(0) 会掩盖负值，用负值判断）
    if limit is not None and (float(limit) - used - pending) < 0:
        status = "over_budget"
    return {
        "department_id": department.id,
        "department_name": department.name,
        "department_code": department.code,
        "budget_limit": limit,
        "used": round(used, 2),
        "pending": round(pending, 2),
        "available": round(available, 2) if available is not None else None,
        "utilization": utilization,
        "status": status,
    }


async def list_departments_budget(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Department).order_by(Department.id))
    departments = result.scalars().all()
    return [await get_department_budget(db, d) for d in departments]


async def check_budget_for_request(db: AsyncSession, purchase: PurchaseRequest) -> dict:
    """单笔采购预算校验：返回 {budget_status, limit, used, pending, available_before, available_after, amount}。"""
    department = await db.get(Department, purchase.department_id) if purchase.department_id else None
    limit = department.budget_limit if department else None
    if department is None or limit is None:
        return {
            "budget_status": "unknown", "limit": None, "used": None, "pending": None,
            "available_before": None, "available_after": None, "amount": float(purchase.total_amount or 0),
        }
    used, pending = await _dept_occupied(db, purchase.department_id)
    # 排除本单自身（避免提交/分析时重复占用）
    amount = float(purchase.total_amount or 0)
    if purchase.status == "approved":
        used -= amount
    elif purchase.status in _OCCUPYING:
        pending -= amount
    available_before = float(limit) - used - pending
    available_after = available_before - amount
    return {
        "budget_status": _status_of(available_after, limit),
        "limit": float(limit),
        "used": round(used, 2),
        "pending": round(pending, 2),
        "available_before": round(available_before, 2),
        "available_after": round(available_after, 2),
        "amount": amount,
    }


async def set_budget_limit(db: AsyncSession, department_id: int, budget_limit: float) -> dict:
    """设置/更新部门年度预算上限。"""
    department = await db.get(Department, department_id)
    if department is None:
        raise LookupError(f"部门不存在: {department_id}")
    if budget_limit < 0:
        raise ValueError("预算上限不能为负数")
    department.budget_limit = budget_limit
    await db.commit()
    await db.refresh(department)
    return await get_department_budget(db, department)
