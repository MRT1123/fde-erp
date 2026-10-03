"""规则引擎与工作流冒烟测试。"""
import pytest

from app.services.risk_rules import compute_rule_score


def test_rule_score_low():
    result = compute_rule_score({"total_amount": 1_000})
    assert result["risk_score"] == 0
    assert result["risk_level"] == "low"


def test_rule_score_high():
    result = compute_rule_score(
        {
            "total_amount": 60_000,
            "first_cooperation": True,
            "over_budget": True,
        }
    )
    assert result["risk_score"] == 75
    assert result["risk_level"] == "high"


@pytest.mark.asyncio
async def test_graph_compiles_and_runs():
    from app.graph.graph import get_compiled_graph

    graph = get_compiled_graph()
    result = await graph.ainvoke(
        {
            "request_id": 1,
            "purchase_request": {"total_amount": 2_000, "supplier_id": None},
        }
    )
    assert result["risk_score"] == 0
    assert result["approval_decision"] == "approve"
    assert result["needs_human_review"] is False
