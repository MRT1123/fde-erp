"""Agent 分析流程：提交采购单后调用 FDE Agent 风险分析并应用结果。

纯逻辑模块，不依赖 Celery；供 direct 模式与 Celery 任务共用。
- 优先调用 fde-agents（Supervisor 多 Agent / LangGraph 编排）
- agent-service 不可用时降级到本地规则引擎（risk_service），保证流程可演示。
"""
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.org import Department
from app.models.purchase import PurchaseItem, PurchaseRequest
from app.models.supplier import Supplier
from app.services import budget_service, purchase_service, risk_service


async def _build_payload(db, purchase: PurchaseRequest) -> dict:
    """构造 Agent 分析所需的采购上下文。"""
    items = (
        await db.execute(
            select(PurchaseItem).where(PurchaseItem.purchase_request_id == purchase.id)
        )
    ).scalars().all()
    supplier_name = ""
    first_cooperation = False
    supplier_risk = False
    if purchase.supplier_id:
        supplier = await db.get(Supplier, purchase.supplier_id)
        if supplier:
            supplier_name = supplier.name
            first_cooperation = bool(supplier.first_cooperation)
            supplier_risk = supplier.risk_level in ("high", "medium")
    department_name = ""
    over_budget = False
    if purchase.department_id:
        dept = await db.get(Department, purchase.department_id)
        department_name = dept.name if dept else ""
        # 预算校验：超预算时作为风险维度传入 FDE（+20 分）
        budget = await budget_service.check_budget_for_request(db, purchase)
        over_budget = budget["budget_status"] == "over_budget"

    return {
        "request_id": purchase.id,
        "title": purchase.title,
        "total_amount": purchase.total_amount,
        "supplier_id": purchase.supplier_id,
        "supplier_name": supplier_name,
        "first_cooperation": first_cooperation,
        "supplier_risk": supplier_risk,
        "department": department_name,
        "purpose": purchase.purpose,
        "over_budget": over_budget,
        "items": [
            {"material_name": it.material_name, "quantity": it.quantity,
             "unit_price": it.unit_price, "amount": it.amount}
            for it in items
        ],
    }


async def run_risk_analysis(request_id: int) -> dict:
    """异步直连执行：Agent 分析 → 应用结果（direct 模式与 Celery 共用）。"""
    async with AsyncSessionLocal() as db:
        purchase = await db.get(PurchaseRequest, request_id)
        if purchase is None:
            return {"ok": False, "error": "purchase request not found"}

        try:
            from app.services import agent_client

            payload = await _build_payload(db, purchase)
            resp = await agent_client.trigger_risk_analysis(request_id, payload)
            # FDE 返回 {request_id, final_result:{...}, summary}，归一化为扁平结构
            fr = resp.get("final_result") or resp
            result = {
                "risk_score": fr.get("risk_score", 0),
                "risk_level": fr.get("risk_level", ""),
                "analysis": fr.get("analysis") or fr.get("risk_analysis") or str(fr),
            }
        except Exception:
            # 降级：本地规则引擎（Agent 服务不可用时的兜底）
            first_cooperation = False
            over_budget = False
            if purchase.supplier_id:
                supplier = await db.get(Supplier, purchase.supplier_id)
                if supplier:
                    first_cooperation = bool(supplier.first_cooperation)
            if purchase.department_id:
                budget = await budget_service.check_budget_for_request(db, purchase)
                over_budget = budget["budget_status"] == "over_budget"
            score, level, dimensions = risk_service.compute_risk_score(
                total_amount=purchase.total_amount,
                first_cooperation=first_cooperation,
                over_budget=over_budget,
            )
            result = {"risk_score": score, "risk_level": level, "analysis": str(dimensions)}

        updated = await purchase_service.apply_agent_result(db, request_id, result)
        return {
            "ok": True,
            "request_no": updated.request_no,
            "status": updated.status,
            "risk_score": updated.risk_score,
            "risk_level": updated.risk_level,
            "needs_human_review": updated.needs_human_review,
        }
