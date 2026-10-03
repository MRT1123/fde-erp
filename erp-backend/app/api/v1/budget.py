"""预算管控 API：部门预算总览、单部门预算明细、设置预算上限。"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.org import Department
from app.models.purchase import PurchaseRequest
from app.services import budget_service

router = APIRouter()


class BudgetLimitIn(BaseModel):
    budget_limit: float


@router.get("/departments")
async def list_budget(db: DbSession):
    """部门预算总览：上限/已用/在途/可用/使用率/状态。"""
    return await budget_service.list_departments_budget(db)


@router.get("/departments/{department_id}")
async def department_budget_detail(department_id: int, db: DbSession):
    """单部门预算总览 + 该部门采购单预算明细。"""
    department = await db.get(Department, department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="部门不存在")
    overview = await budget_service.get_department_budget(db, department)
    result = await db.execute(
        select(PurchaseRequest)
        .where(PurchaseRequest.department_id == department_id)
        .order_by(PurchaseRequest.id.desc())
    )
    requests = []
    for pr in result.scalars().all():
        requests.append({
            "id": pr.id,
            "request_no": pr.request_no,
            "title": pr.title,
            "total_amount": pr.total_amount,
            "status": pr.status,
            "budget_status": pr.budget_status,
            "risk_level": pr.risk_level,
            "created_at": pr.created_at.isoformat() if pr.created_at else None,
        })
    overview["requests"] = requests
    return overview


@router.put("/departments/{department_id}/limit")
async def update_budget_limit(department_id: int, payload: BudgetLimitIn, db: DbSession):
    """设置/更新部门年度预算上限（元）。"""
    try:
        overview = await budget_service.set_budget_limit(db, department_id, payload.budget_limit)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return overview
