"""审批建议 Agent：综合风险分 + 尽调报告给出决策建议。"""
import json

from app.config import settings
from app.services.llm_client import LLMClient


def _normalize_supplier_report(supplier_report) -> dict:
    """归一化尽调报告：LLM 模式下 Supervisor 拼接 context 时可能传入 None / JSON 字符串。"""
    if isinstance(supplier_report, dict):
        return supplier_report
    if isinstance(supplier_report, str):
        try:
            parsed = json.loads(supplier_report)
            if isinstance(parsed, dict):
                return parsed
        except (TypeError, json.JSONDecodeError):
            pass
    return {}


class ApprovalAdvisor:
    """输出「通过/驳回/补充材料/转人工」建议。"""

    def __init__(self) -> None:
        self.llm = LLMClient()

    async def decide(self, risk_score: float, risk_analysis: str, supplier_report: dict) -> dict:
        supplier_report = _normalize_supplier_report(supplier_report)
        # 规则兜底：直接依据风险分
        if risk_score >= settings.RISK_HIGH_THRESHOLD:
            decision = "human"
            reasons = [f"综合风险分 {risk_score:.0f} ≥ {settings.RISK_HIGH_THRESHOLD}，需人工审批"]
        elif risk_score >= settings.RISK_MEDIUM_THRESHOLD:
            decision = "human"
            reasons = [f"综合风险分 {risk_score:.0f}，建议人工复核"]
        else:
            decision = "approve"
            reasons = [f"综合风险分 {risk_score:.0f}，低于自动通过阈值，风险可控"]

        # 尽调风险信号补充
        flags = supplier_report.get("risk_flags") or []
        if flags:
            decision = "human"
            reasons.append(f"供应商尽调发现 {len(flags)} 条风险信号：{flags[:3]}")

        if self.llm.ready:
            try:
                prompt = (
                    "你是采购审批辅助专家。综合风险分与尽调报告，给出审批建议（通过/驳回/补充材料/转人工）"
                    "及 1-3 条理由。\n"
                    f"风险分：{risk_score}，分析：{risk_analysis}，尽调：{supplier_report}"
                )
                text = await self.llm.complete(prompt)
                if text:
                    reasons.append(text)
            except Exception:
                pass

        return {"decision": decision, "reasons": reasons}
