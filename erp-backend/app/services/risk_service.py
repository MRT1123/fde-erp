"""本地兜底风险规则引擎：不依赖 LLM 时按方案规则计算风险分。

维度与权重（对应 FDE_ERP_项目方案.html 5.1）：
- 金额（阶梯分级）：≥50,000 +30；≥200,000 +45；≥500,000 +60
- 新供应商（首次合作）      +25
- 品类与部门历史不符       +20
- 供应商尽调风险          +25
- 同一供应商短期多次采购    +15
- 超预算                 +20
"""
from app.core.config import settings


def compute_risk_score(
    total_amount: float,
    first_cooperation: bool = False,
    category_mismatch: bool = False,
    supplier_risk: bool = False,
    frequency_risk: bool = False,
    over_budget: bool = False,
) -> tuple[float, str, dict]:
    """返回 (risk_score, risk_level, dimensions)。"""
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
        "new_supplier": 25 if first_cooperation else 0,
        "category": 20 if category_mismatch else 0,
        "supplier_risk": 25 if supplier_risk else 0,
        "frequency": 15 if frequency_risk else 0,
        "budget": 20 if over_budget else 0,
    }
    score = sum(dimensions.values())
    level = "high" if score >= settings.RISK_HIGH_THRESHOLD else (
        "medium" if score >= settings.RISK_MEDIUM_THRESHOLD else "low"
    )
    return score, level, dimensions
