"""Supervisor 主图：意图识别 Agent 分发任务给子图（多 Agent 协作 / Supervisor 模式）。

流程：
    START → supervisor（意图识别：LLM 看请求与历史，决定调用哪个子 Agent 工具）
          → tools（执行被选中的子图）→ supervisor（继续决策）
          → finalize（聚合子图结果 → 返回 ERP）→ END
"""
import json
from typing import Literal

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from app.graph.state import SUBGRAPH_OUTPUT_FIELDS, SupervisorState
from app.graph.supervisor.tools import (
    ADVICE_SUBGRAPH,
    ANOMALY_SUBGRAPH,
    DILIGENCE_SUBGRAPH,
    RISK_SUBGRAPH,
    SUB_AGENT_TOOLS,
)
from app.services.llm_client import llm_client

SUPERVISOR_SYSTEM_PROMPT = """你是采购风控协调 Agent（Supervisor）。ERP 系统会传来一份采购申请及上下文。
你的职责是【意图识别】：判断本次任务需要调用哪些专业子 Agent（子图），并按序分发，而不是自己直接给出完整结论。

可用子 Agent（通过工具调用）：
1. analyze_risk     —— 风险评估（必调）：计算综合风险评分、风险级别、维度得分
2. supplier_diligence —— 供应商尽调：搜索舆情、风险信号、尽调报告
3. approval_advice  —— 审批建议：综合风险分与尽调报告给出 approve/reject/human 建议
4. detect_anomaly   —— 异常检测：基于历史采购识别拆分订单等异常

执行策略：
- 先 analyze_risk；如采购单有供应商信息，再 supplier_diligence；
- 拿到前两者结果后调用 approval_advice 生成审批建议；
- 如提供了 history 字段，调用 detect_anomaly；
- 完成后用中文总结一句最终结论（含风险分、是否需人工审批）。
"""


async def _rule_based_supervisor(state: SupervisorState):
    """无 LLM 时的规则路由降级：按固定意图顺序分发全部子图，保证多 Agent 协作可演示。"""
    pr = state.get("purchase_request", {})
    risk = await RISK_SUBGRAPH.ainvoke({"purchase_request": pr})
    diligence = await DILIGENCE_SUBGRAPH.ainvoke({"purchase_request": pr})
    context = {**risk, **diligence}
    advice = await ADVICE_SUBGRAPH.ainvoke(context)
    anomaly = await ANOMALY_SUBGRAPH.ainvoke({"history": pr.get("history", [])})
    combined = {**risk, **diligence, **advice, **anomaly}
    return {
        "messages": [AIMessage(content="（规则路由完成）", name="supervisor")],
        **combined,
    }


async def supervisor_node(state: SupervisorState):
    """意图识别节点：LLM 绑定子 Agent 工具，自主决定分发；无 LLM 走规则路由。"""
    llm = llm_client.get_chat_model()
    if llm is None:
        return await _rule_based_supervisor(state)

    messages = list(state.get("messages", []))
    llm_with_tools = llm.bind_tools(SUB_AGENT_TOOLS)
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}


def _should_continue(state: SupervisorState) -> Literal["tools", "finalize"]:
    """条件路由：Supervisor 还有工具调用就继续分发；否则进入最终聚合。"""
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return "finalize"


async def finalize_node(state: SupervisorState):
    """聚合所有子图回写字段，生成 ERP 可用的结构化 final_result。

    按工具名精确聚合，避免子图返回中的同名业务字段（如 supplier_report.risk_level）
    覆盖风险分析的 risk_level。
    """
    fields: dict = {}
    for msg in state.get("messages", []):
        if getattr(msg, "type", "") != "tool":
            continue
        try:
            data = json.loads(msg.content)
        except (TypeError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        name = getattr(msg, "name", "")
        if name == "analyze_risk":
            for key in ("risk_score", "risk_level", "dimensions", "risk_analysis"):
                if key in data:
                    fields.setdefault(key, data[key])
        elif name == "supplier_diligence":
            if "supplier_report" in data:
                fields.setdefault("supplier_report", data["supplier_report"])
        elif name == "approval_advice":
            for key in ("approval_decision", "decision_reasons", "needs_human_review"):
                if key in data:
                    fields.setdefault(key, data[key])
        elif name == "detect_anomaly":
            if "anomaly_alerts" in data:
                fields.setdefault("anomaly_alerts", data["anomaly_alerts"])
    # 保留 rule 模式直接回写的字段
    for key in SUBGRAPH_OUTPUT_FIELDS:
        if key in state and key not in fields:
            fields[key] = state[key]
    # 注意：final_result 必须是独立 dict，不能引用 fields 自身（避免循环引用导致序列化递归）
    fields["final_result"] = {k: v for k, v in fields.items() if k != "final_result"}
    return fields


def build_supervisor_graph() -> StateGraph:
    """构建 Supervisor 主图。"""
    g = StateGraph(SupervisorState)
    g.add_node("supervisor", supervisor_node)
    g.add_node("tools", ToolNode(SUB_AGENT_TOOLS))
    g.add_node("finalize", finalize_node)

    g.add_edge(START, "supervisor")
    g.add_conditional_edges(
        "supervisor",
        _should_continue,
        {"tools": "tools", "finalize": "finalize"},
    )
    g.add_edge("tools", "supervisor")
    g.add_edge("finalize", END)
    return g
