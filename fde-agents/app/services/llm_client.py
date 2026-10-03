"""LLM 客户端：支持 OpenAI 兼容接口（OpenAI / DeepSeek / 豆包），基于 langchain-openai。

- 未配置 OPENAI_API_KEY 时 ready=False，Supervisor 自动降级为「规则路由」，
  仍能按意图执行全部子图，保证无 LLM 也能演示多 Agent 协作。
- 配置 API Key 后支持 bind_tools，Supervisor 通过工具调用分发任务给子 Agent。
"""
from typing import Optional

from app.config import settings


class LLMClient:
    def __init__(self) -> None:
        self.ready = bool(settings.OPENAI_API_KEY)
        self.model = settings.LLM_MODEL
        self.base_url = settings.OPENAI_BASE_URL or None
        self.temperature = settings.LLM_TEMPERATURE
        self._chat = None

    def get_chat_model(self, temperature: Optional[float] = None):
        """返回 langchain ChatOpenAI 实例（惰性创建）；未配置 Key 返回 None。"""
        if not self.ready:
            return None
        if self._chat is None:
            from langchain_openai import ChatOpenAI

            self._chat = ChatOpenAI(
                model=self.model,
                api_key=settings.OPENAI_API_KEY,
                base_url=self.base_url,
                temperature=temperature if temperature is not None else self.temperature,
            )
        return self._chat

    async def complete(self, prompt: str, max_tokens: int = 500) -> str:
        """调用 LLM 完成文本生成；未配置 Key 返回空串。"""
        llm = self.get_chat_model()
        if llm is None:
            return ""
        resp = await llm.ainvoke(prompt, max_tokens=max_tokens)
        return str(resp.content)


llm_client = LLMClient()
