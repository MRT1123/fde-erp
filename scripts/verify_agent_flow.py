"""Supervisor 多 Agent 工作流验证脚本。

默认走规则路由模式（强制空 LLM Key）；加 --llm 参数时使用真实 DeepSeek Key。
验证：主图 ainvoke 后 final_result 聚合了风险分析、供应商尽调、审批建议、
异常检测四个子图的结果。
用法：
    python scripts/verify_agent_flow.py          # 规则路由模式
    python scripts/verify_agent_flow.py --llm    # DeepSeek LLM 模式
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "fde-agents"))

if "--llm" not in sys.argv:
    # 规则路由模式：必须在 import app 之前强制清空 Key
    os.environ["OPENAI_API_KEY"] = ""

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.graph import get_compiled_graph
from app.graph.supervisor.graph import SUPERVISOR_SYSTEM_PROMPT


async def main() -> None:
    graph = get_compiled_graph()
    purchase_request = {
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
    messages = [
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
        HumanMessage(content=f"请对以下采购申请执行风控分析：{purchase_request}"),
    ]
    result = await graph.ainvoke(
        {"request_id": 1, "purchase_request": purchase_request, "messages": messages}
    )
    final = result.get("final_result") or {}
    print("== final_result ==")
    for key in ("risk_score", "risk_level", "approval_decision", "decision_reasons",
                "needs_human_review", "risk_analysis", "supplier_report", "anomaly_alerts"):
        print(f"  {key}: {final.get(key)}")

    assert "risk_score" in final, "缺少 risk_score（风险分析子图未执行）"
    assert "supplier_report" in final, "缺少 supplier_report（尽调子图未执行）"
    assert "approval_decision" in final, "缺少 approval_decision（建议子图未执行）"
    assert "anomaly_alerts" in final, "缺少 anomaly_alerts（异常检测子图未执行）"
    print("\n=== SUPERVISOR 多 Agent 工作流验证通过 ===")


if __name__ == "__main__":
    asyncio.run(main())
