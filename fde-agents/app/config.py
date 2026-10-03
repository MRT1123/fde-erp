"""FDE Agent 服务配置。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "FDE 智能风控 Agent 服务"
    DEBUG: bool = True

    # ERP 后端
    ERP_API_URL: str = "http://localhost:8000"

    # LLM
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""  # 兼容 Kimi/DeepSeek 等
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.2

    # 公开搜索（供应商尽调）
    SERPER_API_KEY: str = ""
    SEARCH_API_KEY: str = ""

    # 风险阈值（与 ERP 保持一致）
    RISK_HIGH_THRESHOLD: float = 70.0
    RISK_MEDIUM_THRESHOLD: float = 40.0

    # Redis（LangGraph checkpointer 可选）
    REDIS_URL: str = "redis://localhost:6379/1"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
