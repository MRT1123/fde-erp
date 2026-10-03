"""数据看板 API：采购统计、风险分布、供应商评级分布。"""
from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import DbSession
from app.models.approval import Approval
from app.models.purchase import PurchaseRequest
from app.models.supplier import Supplier

router = APIRouter()


@router.get("/summary")
async def dashboard_summary(db: DbSession):
    """概览统计。"""
    total_requests = (await db.execute(select(func.count(PurchaseRequest.id)))).scalar() or 0
    approved = (
        await db.execute(select(func.count(PurchaseRequest.id)).where(PurchaseRequest.status == "approved"))
    ).scalar() or 0
    total_amount = (
        await db.execute(select(func.coalesce(func.sum(PurchaseRequest.total_amount), 0)))
    ).scalar() or 0
    high_risk = (
        await db.execute(
            select(func.count(PurchaseRequest.id)).where(PurchaseRequest.risk_level == "high")
        )
    ).scalar() or 0
    supplier_count = (await db.execute(select(func.count(Supplier.id)))).scalar() or 0

    return {
        "total_requests": total_requests,
        "approved": approved,
        "pending_approval": total_requests - approved,
        "total_amount": total_amount,
        "high_risk_requests": high_risk,
        "supplier_count": supplier_count,
    }


@router.get("/risk-distribution")
async def risk_distribution(db: DbSession):
    """按风险等级统计采购单分布。"""
    rows = (
        await db.execute(
            select(PurchaseRequest.risk_level, func.count(PurchaseRequest.id))
            .group_by(PurchaseRequest.risk_level)
        )
    ).all()
    return {level or "unknown": count for level, count in rows}


@router.get("/status-distribution")
async def status_distribution(db: DbSession):
    """按审批状态统计采购单分布。"""
    rows = (
        await db.execute(
            select(PurchaseRequest.status, func.count(PurchaseRequest.id))
            .group_by(PurchaseRequest.status)
        )
    ).all()
    return {status or "unknown": count for status, count in rows}


@router.get("/supplier-risk")
async def supplier_risk(db: DbSession):
    """供应商风险等级分布。"""
    rows = (
        await db.execute(
            select(Supplier.risk_level, func.count(Supplier.id))
            .group_by(Supplier.risk_level)
        )
    ).all()
    return {level or "unknown": count for level, count in rows}


@router.get("/approval-timeline")
async def approval_timeline(db: DbSession, limit: int = 10):
    """最近审批记录（供审批趋势展示）。"""
    rows = (
        await db.execute(
            select(Approval.id, Approval.approval_no, Approval.status, Approval.decision,
                   Approval.risk_score_snapshot, Approval.created_at)
            .order_by(Approval.id.desc())
            .limit(limit)
        )
    ).all()
    return [
        {
            "id": r.id,
            "approval_no": r.approval_no,
            "status": r.status,
            "decision": r.decision,
            "risk_score": r.risk_score_snapshot,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
