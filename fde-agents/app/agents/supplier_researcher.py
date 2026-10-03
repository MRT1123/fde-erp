"""供应商尽调 Agent：联网搜索工商信息、舆情、法律风险。"""
from app.services.llm_client import LLMClient
from app.services.web_search import search_supplier_news


class SupplierResearcher:
    """生成供应商背景报告。

    TODO: 接入企业信用 API（企查查/天眼查）获取工商信息；
    当前先通过公开搜索收集舆情风险，LLM 汇总为报告。
    """

    def __init__(self) -> None:
        self.llm = LLMClient()

    async def research(self, supplier_id: int, supplier_name: str) -> dict:
        news = await search_supplier_news(supplier_name)
        risk_flags: list[str] = []
        for item in news:
            text = f"{item.get('title', '')} {item.get('snippet', '')}"
            for keyword in ("被执行人", "失信", "处罚", "诉讼", "负面", "欠薪", "立案"):
                if keyword in text:
                    risk_flags.append(f"{keyword}: {item.get('title', '')}")

        report_content = ""
        if self.llm.ready:
            try:
                report_content = await self.llm.complete(
                    "你是企业尽调专家。请基于以下供应商舆情信息输出一份尽调报告（中文，300 字以内），"
                    "包含风险信号列表与综合风险判断。\n"
                    f"供应商：{supplier_name}\n舆情：{news}"
                )
            except Exception:
                pass

        risk_level = "high" if len(risk_flags) >= 3 else ("medium" if risk_flags else "low")
        return {
            "supplier_id": supplier_id,
            "supplier_name": supplier_name,
            "news": news,
            "risk_flags": risk_flags,
            "risk_level": risk_level,
            "report_content": report_content or (f"发现 {len(risk_flags)} 条风险信号" if risk_flags else "未发现明显风险信号"),
        }
