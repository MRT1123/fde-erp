"""节点：低风险自动通过。"""
from typing import Any


async def auto_approve(state: dict[str, Any]) -> dict[str, Any]:
    """低风险采购单自动通过。"""
    return {
        "needs_human_review": False,
        "approval_decision": "approve",
    }
