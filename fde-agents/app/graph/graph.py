"""LangGraph 工作流入口（多 Agent 协作 / Supervisor 模式）。

主图 = Supervisor 意图识别 Agent + 子图分发；对外暴露编译后的可执行图。
"""
from langgraph.graph import StateGraph

from app.graph.supervisor.graph import build_supervisor_graph


def build_workflow() -> StateGraph:
    """返回 Supervisor 主图（未编译）。"""
    return build_supervisor_graph()


def get_compiled_graph():
    """返回可执行图（支持 ainvoke / invoke）。"""
    return build_supervisor_graph().compile()
