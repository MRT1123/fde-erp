"""采购申请服务：创建、提交审批（触发 Agent）、撤回。"""
import datetime as dt

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.audit import AuditLog
from app.models.org import Department, Employee
from app.models.purchase import PurchaseItem, PurchaseRequest
from app.schemas.purchase import PurchaseRequestCreate
from app.services import agent_client
from app.services.audit_service import record_audit
from typing import Optional


async def _gen_request_no(db: AsyncSession) -> str:
    """生成申请单号：PR + yyyymmdd + 3 位序号（按当天最大序号递增，兼容删除造成的空洞）。"""
    today = dt.date.today().strftime("%Y%m%d")
    prefix = f"PR{today}"
    rows = (
        await db.execute(select(PurchaseRequest.request_no).where(PurchaseRequest.request_no.like(f"{prefix}%")))
    ).scalars().all()
    max_seq = 0
    for no in rows:
        suffix = no[len(prefix):]
        if suffix.isdigit():
            max_seq = max(max_seq, int(suffix))
    seq = max_seq + 1
    return f"{prefix}{seq:03d}"


async def create_purchase_request(
    db: AsyncSession, payload: PurchaseRequestCreate,
    current_user: Optional[Employee] = None,
) -> PurchaseRequest:
    """创建采购申请草稿。

    applicant_id / department_id 优先级：调用方传入 → 当前登录用户 → 员工/部门表第一条（兜底）。
    """
    request_no = await _gen_request_no(db)
    total = sum(item.quantity * (item.unit_price or 0) for item in payload.items)

    applicant_id = payload.applicant_id or (current_user.id if current_user else None)
    department_id = payload.department_id or (current_user.department_id if current_user else None)
    if not applicant_id:
        applicant = (await db.execute(select(Employee).order_by(Employee.id).limit(1))).scalars().first()
        applicant_id = applicant.id if applicant else 1
    if not department_id:
        department = (await db.execute(select(Department).order_by(Department.id).limit(1))).scalars().first()
        department_id = department.id if department else 1

    obj = PurchaseRequest(
        request_no=request_no,
        title=payload.title,
        applicant_id=applicant_id,
        department_id=department_id,
        supplier_id=payload.supplier_id,
        total_amount=total,
        purpose=payload.purpose,
        status="draft",
    )
    for item in payload.items:
        obj.items.append(
            PurchaseItem(
                material_id=item.material_id,
                material_name=item.material_name,
                spec=item.spec,
                quantity=item.quantity,
                unit_price=item.unit_price,
                amount=item.quantity * (item.unit_price or 0),
                remark=item.remark,
            )
        )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    await record_audit(db, actor_type="user", action="create", entity_type="purchase_request", entity_id=obj.id)
    return obj


async def submit_for_review(db: AsyncSession, request_id: int) -> PurchaseRequest:
    """提交审批：状态转 analyzing，并异步触发 FDE Agent 风险分析。"""
    obj = await db.get(PurchaseRequest, request_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    if obj.status != "draft":
        raise HTTPException(status_code=409, detail=f"当前状态 {obj.status} 不可提交")

    obj.status = "analyzing"
    obj.submitted_at = dt.datetime.now(dt.timezone.utc)
    await db.commit()
    await db.refresh(obj)

    # 触发 Agent 分析：配置 direct 时直接同步调用（本地开发/测试），celery 时异步派发
    if settings.AGENT_TRIGGER_MODE == "celery":
        from app.tasks.agent_triggers import trigger_risk_analysis

        trigger_risk_analysis.delay(request_id)
    else:
        from app.services.agent_flow import run_risk_analysis

        await run_risk_analysis(request_id)
    return obj


async def withdraw(db: AsyncSession, request_id: int) -> PurchaseRequest:
    """撤回采购申请（仅 draft/pending_approval 可撤回）。"""
    obj = await db.get(PurchaseRequest, request_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    if obj.status not in {"draft", "pending_approval"}:
        raise HTTPException(status_code=409, detail="当前状态不可撤回")
    obj.status = "withdrawn"
    await db.commit()
    await db.refresh(obj)
    return obj


async def apply_agent_result(db: AsyncSession, request_id: int, result: dict) -> PurchaseRequest:
    """应用 Agent 分析结果：更新风险评分并路由。

    路由规则（与方案一致）：
    - risk_score < 40：低风险，Agent 建议通过 → 自动放行
    - 40 <= risk_score < 70：中风险 → 默认人工审批
    - risk_score >= 70：高风险 → 强制人工审批，创建飞书审批实例
    """
    obj = await db.get(PurchaseRequest, request_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    if obj.status != "analyzing":
        raise HTTPException(status_code=409, detail=f"当前状态 {obj.status} 不可接收 Agent 结果")

    risk_score = float(result.get("risk_score", 0))
    obj.risk_score = risk_score
    obj.risk_level = (
        "high" if risk_score >= settings.RISK_HIGH_THRESHOLD
        else "medium" if risk_score >= settings.RISK_MEDIUM_THRESHOLD
        else "low"
    )
    obj.agent_summary = result.get("analysis", "")

    # 预算校验落库：budget_status = ok / over_budget / unknown
    from app.services.budget_service import check_budget_for_request

    budget = await check_budget_for_request(db, obj)
    obj.budget_status = budget["budget_status"]

    if risk_score < settings.RISK_MEDIUM_THRESHOLD:
        # 低风险：自动通过
        obj.needs_human_review = False
        obj.status = "approved"
        await db.commit()
        await db.refresh(obj)
        await record_audit(
            db, action="auto_approve", entity_type="purchase_request", entity_id=obj.id,
            detail={"risk_score": risk_score, "risk_level": obj.risk_level},
        )
        return obj

    # 中/高风险：进入人工审批（>=70 强制，40-69 默认人工）
    obj.needs_human_review = risk_score >= settings.RISK_MEDIUM_THRESHOLD
    obj.status = "pending_approval"
    await db.commit()
    await db.refresh(obj)

    from app.services.approval_service import _new_approval

    await _new_approval(db, obj)
    await db.refresh(obj)
    await record_audit(
        db, action="route_to_human", entity_type="purchase_request", entity_id=obj.id,
        detail={"risk_score": risk_score, "risk_level": obj.risk_level,
                "needs_human_review": obj.needs_human_review},
    )
    return obj
