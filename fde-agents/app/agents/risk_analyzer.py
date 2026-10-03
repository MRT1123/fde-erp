"""风险分析 Agent：评估采购单风险。"""
from app.services.llm_client import LLMClient
from app.services.risk_rules import compute_rule_score


class RiskAnalyzer:
    """综合规则引擎 + LLM 分析采购单风险。

    优先使用本地规则引擎（可离线、可演示），配置 LLM 后补充自然语言分析。
    """

    def __init__(self) -> None:
        self.llm = LLMClient()

    async def analyze(self, purchase_request: dict) -> dict:
        rule_result = compute_rule_score(purchase_request)
        score = rule_result["risk_score"]
        dimensions = rule_result["dimensions"]

        analysis = ""
        if self.llm.ready:
            try:
                analysis = await self.llm.complete(
                    "你是企业采购风控专家。请基于以下采购单与各维度风险分，输出 3-5 条风险点说明，"
                    "简洁中文，每条不超过 30 字。\n"
                    f"采购单：{purchase_request}\n各维度分：{dimensions}"
                )
            except Exception:
                analysis = rule_result["summary"]

        return {
            "risk_score": score,
            "risk_level": rule_result["risk_level"],
            "dimensions": dimensions,
            "analysis": analysis or rule_result["summary"],
        }
