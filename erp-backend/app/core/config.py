"""应用配置：使用 pydantic-settings 从环境变量 / .env 读取。"""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 应用
    APP_NAME: str = "ERP 智能采购管理系统"
    APP_ENV: str = "dev"  # dev / test / prod
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # 安全
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8
    JWT_ALGORITHM: str = "HS256"

    # 数据库
    DATABASE_URL: str = "postgresql+asyncpg://erp:erp_pass@localhost:5432/erp_db"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # FDE Agent 服务
    AGENT_SERVICE_URL: str = "http://localhost:8001"
    AGENT_SERVICE_TIMEOUT: float = 120.0
    AGENT_TRIGGER_MODE: str = "direct"  # direct=提交时直接触发（本地开发）；celery=异步任务队列

    # 飞书
    FEISHU_APP_ID: str = ""
    FEISHU_APP_SECRET: str = ""
    FEISHU_APPROVAL_DEFINITION_CODE: str = ""  # 审批定义 code
    FEISHU_ENCRYPT_KEY: str = ""  # 事件订阅加密密钥（可选，配置后解密回调内容）
    FEISHU_VERIFICATION_TOKEN: str = ""  # 事件订阅验证令牌（可选，配置后校验回调来源）

    # 风险规则默认阈值
    RISK_HIGH_THRESHOLD: float = 70.0      # >= 70 强制人工审批
    RISK_MEDIUM_THRESHOLD: float = 40.0    # >= 40 建议人工审批
    APPROVAL_TIMEOUT_HOURS: int = 48       # 审批超时升级
    ESCALATION_REMIND_HOURS: int = 4       # 超时前提醒

    # CORS
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
