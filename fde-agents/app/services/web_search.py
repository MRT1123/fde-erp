"""公开信息搜索：供应商舆情收集。

- 配置 SERPER_API_KEY 时走 Serper.dev Google 搜索（真实舆情）；
- 未配置 Key 时返回空列表（离线演示模式，不影响工作流）。
也可配置 SEARCH_API_KEY 复用同一搜索端点。
"""
import httpx

from app.config import settings


async def search_supplier_news(supplier_name: str) -> list[dict]:
    """搜索供应商相关舆情，返回 [{title, snippet, link, date}]。"""
    api_key = settings.SERPER_API_KEY or settings.SEARCH_API_KEY
    if not api_key:
        return []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": f"{supplier_name} 公司 新闻 风险", "gl": "cn", "hl": "zh-cn", "num": 8},
            )
            resp.raise_for_status()
            data = resp.json()
        items = []
        for item in data.get("organic", []) or []:
            items.append(
                {
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "link": item.get("link", ""),
                    "date": item.get("date", ""),
                }
            )
        return items
    except Exception:
        return []
