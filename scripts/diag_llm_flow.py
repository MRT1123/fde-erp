"""LLM 模式 Supervisor 调用链诊断。"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "fde-agents"))

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.graph import get_compiled_graph
from app.graph.supervisor.graph import SUPERVISOR_SYSTEM_PROMPT


async def main() -> None:
    pr = {
        "title": "采购服务器50台",
        "total_amount": 600000,
        "supplier_id": 1,
        "supplier_name": "测试供应商A",
        "purpose": "扩容机房",
        "items": [{"material_name": "服务器", "quantity": 50, "unit_price": 12000}],
        "history": [
            {"supplier_id": 1, "amount": 100000, "created_at": "2026-09-01"},
            {"supplier_id": 1, "amount": 200000, "created_at": "2026-09-05"},
            {"supplier_id": 1, "amount": 150000, "created_at": "2026-09-10"},
        ],
    }
    graph = get_compiled_graph()
    msgs = [
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
        HumanMessage(content=f"请对以下采购申请执行风控分析：{json.dumps(pr, ensure_ascii=False)}"),
    ]
    result = await graph.ainvoke({"request_id": 1, "purchase_request": pr, "messages": msgs})
    print("=== MESSAGE TRACE ===")
    for m in result.get("messages", []):
        t = getattr(m, "type", "")
        if t == "ai":
            tc = getattr(m, "tool_calls", None)
            names = [c["name"] for c in tc] if tc else None
            print(f"AI tool_calls={names} content={str(getattr(m, 'content', ''))[:100]}")
        elif t == "tool":
            print(f"TOOL {m.name}: {str(m.content)[:200]}")
    print()
    fr = result.get("final_result") or {}
    print("final keys:", list(fr.keys()))
    print("risk_score=", fr.get("risk_score"), "risk_level=", fr.get("risk_level"))
    print("decision=", fr.get("approval_decision"))


if __name__ == "__main__":
    asyncio.run(main())
