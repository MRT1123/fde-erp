"""本地风险规则引擎（与 ERP 端一致，双端可独立计算）。"""
from app.config import settings


def compute_rule_score(purchase_request: dict) -> dict:
    """按方案 5.1 维度计算风险分（与 ERP 端 risk_service 保持一致）。"""
    total_amount = float(purchase_request.get("total_amount") or 0)
    if total_amount >= 500_000:
        amount_score = 60
    elif total_amount >= 200_000:
        amount_score = 45
    elif total_amount >= 50_000:
        amount_score = 30
    else:
        amount_score = 0
    dimensions = {
        "amount": amount_score,
        "new_supplier": 25 if purchase_request.get("first_cooperation") else 0,
        "category": 20 if purchase_request.get("category_mismatch") else 0,
        "supplier_risk": 25 if purchase_request.get("supplier_risk") else 0,
        "frequency": 15 if purchase_request.get("frequency_risk") else 0,
        "budget": 20 if purchase_request.get("over_budget") else 0,
    }
    score = sum(dimensions.values())
    level = "high" if score >= settings.RISK_HIGH_THRESHOLD else (
        "medium" if score >= settings.RISK_MEDIUM_THRESHOLD else "low"
    )
    active = [k for k, v in dimensions.items() if v > 0]
    summary = f"综合风险分 {score}（{level}）。触发维度：{', '.join(active) if active else '无'}"
    return {"risk_score": score, "risk_level": level, "dimensions": dimensions, "summary": summary}
