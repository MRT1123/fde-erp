"""风险规则引擎单元测试（不依赖数据库）。"""
from app.services.risk_service import compute_risk_score


def test_low_risk_auto_approve():
    score, level, _ = compute_risk_score(total_amount=5_000)
    assert score < 40
    assert level == "low"


def test_high_risk_human_review():
    score, level, _ = compute_risk_score(
        total_amount=60_000, first_cooperation=True, over_budget=True
    )
    assert score >= 70
    assert level == "high"


def test_dimensions_sum():
    _, _, dimensions = compute_risk_score(
        total_amount=60_000, first_cooperation=True, over_budget=True
    )
    assert dimensions["amount"] == 30
    assert dimensions["new_supplier"] == 25
    assert dimensions["budget"] == 20
