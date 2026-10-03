"""节点：供应商尽调。"""
from typing import Any

from app.agents.supplier_researcher import SupplierResearcher


async def research_supplier(state: dict[str, Any]) -> dict[str, Any]:
    """联网搜索供应商工商信息、舆情、法律风险，生成尽调报告。"""
    pr = state.get("purchase_request") or {}
    supplier_id = pr.get("supplier_id")
    if not supplier_id:
        return {"supplier_report": {"skip": True, "reason": "无指定供应商"}}

    researcher = SupplierResearcher()
    report = await researcher.research(supplier_id, pr.get("supplier_name", ""))
    return {"supplier_report": report}
