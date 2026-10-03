"""审批服务：审批通过/驳回、飞书回调处理、超时升级。"""
import datetime as dt
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.approval import Approval, ApprovalAction
from app.models.org import Department, Employee
from app.models.purchase import PurchaseRequest
from app.services.feishu_service import feishu_service


async def _resolve_approver(db: AsyncSession, department_id: Optional[int]) -> Optional[Employee]:
    """确定审批人：优先部门负责人，其次部门审批角色员工，最后管理员。"""
    if department_id:
        dept = await db.get(Department, department_id)
        if dept and dept.manager_id:
            manager = await db.get(Employee, dept.manager_id)
            if manager and manager.status == "active":
                return manager
    # 兜底：部门审批角色 / 管理员
    result = await db.execute(
        select(Employee).where(
            Employee.status == "active",
            Employee.role.in_(["department_approver", "senior_approver", "admin"]),
        ).limit(1)
    )
    return result.scalar_one_or_none()


async def _new_approval(db: AsyncSession, purchase: PurchaseRequest) -> Approval:
    """为采购单创建审批实例（高风险/中风险人工审批），并联动飞书。"""
    approver = await _resolve_approver(db, purchase.department_id)
    approval = Approval(
        purchase_request_id=purchase.id,
        approval_no=f"APV{purchase.request_no}",
        status="pending",
        approver_id=approver.id if approver else None,
        risk_score_snapshot=purchase.risk_score,
        started_at=dt.datetime.now(dt.timezone.utc),
        timeout_at=dt.datetime.now(dt.timezone.utc)
        + dt.timedelta(hours=settings.APPROVAL_TIMEOUT_HOURS),
    )
    db.add(approval)
    await db.commit()
    await db.refresh(approval)

    # 联动飞书：创建审批实例（未配置飞书时静默跳过，返回 None）
    if approver and approver.feishu_user_id:
        # 申请人姓名快照 + 飞书发起人关联：取采购单申请人，避免暂存 applicant_id
        applicant = None
        if purchase.applicant_id:
            applicant = await db.get(Employee, purchase.applicant_id)
        applicant_name = applicant.name if applicant else str(purchase.applicant_id)
        initiator_open_id = applicant.feishu_user_id if applicant else None
        instance_code = await feishu_service.create_approval_instance(
            request_no=purchase.request_no,
            applicant_name=applicant_name,
            amount=purchase.total_amount,
            risk_score=purchase.risk_score or 0,
            analysis=purchase.agent_summary or "",
            approver_user_ids=[approver.feishu_user_id],
            initiator_open_id=initiator_open_id,
        )
        if instance_code:
            approval.feishu_instance_code = instance_code
            purchase.feishu_instance_code = instance_code
            await db.commit()
            await db.refresh(approval)

    await db.execute(
        ApprovalAction.__table__.insert().values(
            approval_id=approval.id,
            action="submit",
            from_status="draft",
            to_status="pending_approval",
            operator_id=approver.id if approver else None,
        )
    )
    await db.commit()
    return approval


async def approve(db: AsyncSession, approval_id: int, comment: str | None = None,
                  operator_id: Optional[int] = None) -> Approval:
    approval = await db.get(Approval, approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="审批记录不存在")
    if approval.status not in {"pending", "approving"}:
        raise HTTPException(status_code=409, detail="审批已结束")

    approval.status = "approved"
    approval.decision = "approved"
    approval.comment = comment
    approval.finished_at = dt.datetime.now(dt.timezone.utc)
    await db.flush()

    purchase = await db.get(PurchaseRequest, approval.purchase_request_id)
    if purchase:
        purchase.status = "approved"
    db.add(
        ApprovalAction(
            approval_id=approval.id,
            action="approve",
            operator_id=operator_id,
            comment=comment,
            from_status="pending_approval",
            to_status="approved",
        )
    )
    await db.commit()
    await db.refresh(approval)

    # 通知申请人（未配置飞书时静默跳过）
    if purchase:
        await _notify_result(purchase, "已通过", comment)
    return approval


async def reject(db: AsyncSession, approval_id: int, reason: str,
                 operator_id: Optional[int] = None) -> Approval:
    approval = await db.get(Approval, approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="审批记录不存在")
    if approval.status not in {"pending", "approving"}:
        raise HTTPException(status_code=409, detail="审批已结束")

    approval.status = "rejected"
    approval.decision = "rejected"
    approval.comment = reason
    approval.finished_at = dt.datetime.now(dt.timezone.utc)
    await db.flush()

    purchase = await db.get(PurchaseRequest, approval.purchase_request_id)
    if purchase:
        purchase.status = "rejected"
    db.add(
        ApprovalAction(
            approval_id=approval.id,
            action="reject",
            operator_id=operator_id,
            comment=reason,
            from_status="pending_approval",
            to_status="rejected",
        )
    )
    await db.commit()
    await db.refresh(approval)

    if purchase:
        await _notify_result(purchase, "已驳回", reason)
    return approval


async def _notify_result(purchase: PurchaseRequest, result_text: str, comment: Optional[str]) -> None:
    """审批结果飞书通知（申请人 feishu_user_id）。"""
    applicant = await _get_applicant(purchase)
    if not applicant or not applicant.feishu_user_id:
        return
    text = (
        f"【采购审批{result_text}】{purchase.request_no} {purchase.title}\n"
        f"金额：{purchase.total_amount} 元\n风险分：{purchase.risk_score}\n"
        f"意见：{comment or '-'}"
    )
    await feishu_service.send_message(applicant.feishu_user_id, text)


async def _get_applicant(purchase: PurchaseRequest):
    from sqlalchemy.orm import selectinload

    from app.core.database import AsyncSessionLocal
    from app.models.org import Employee

    async with AsyncSessionLocal() as db:
        emp = await db.get(Employee, purchase.applicant_id)
        return emp


async def handle_feishu_callback(db: AsyncSession, feishu_code: str, status: str, comment: str = ""):
    """飞书审批回调：按 status 更新审批与采购单。"""
    result = await db.execute(select(Approval).where(Approval.feishu_instance_code == feishu_code))
    approval = result.scalar_one_or_none()
    if approval is None:
        raise ValueError(f"未找到飞书审批实例 {feishu_code}")

    if status == "APPROVED":
        await approve(db, approval.id, comment or "飞书审批通过")
    elif status == "REJECTED":
        await reject(db, approval.id, comment or "飞书审批驳回")
    else:
        # CANCELED / REVOKED 等状态：仅记录，不改变主流程
        pass


async def escalate_timeout(db: AsyncSession) -> int:
    """超时检测任务：将超时未处理的审批升级。返回处理数量。"""
    now = dt.datetime.now(dt.timezone.utc)
    result = await db.execute(
        select(Approval).where(
            Approval.status.in_(["pending", "approving"]),
            Approval.timeout_at < now,
        )
    )
    count = 0
    for approval in result.scalars().all():
        approval.status = "escalated"
        approval.escalated_at = now
        purchase = await db.get(PurchaseRequest, approval.purchase_request_id)
        if purchase:
            purchase.status = "escalated"
        db.add(
            ApprovalAction(
                approval_id=approval.id,
                action="escalate",
                from_status="pending_approval",
                to_status="escalated",
            )
        )
        count += 1
    await db.commit()
    return count
