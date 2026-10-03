"""FastAPI 应用入口。"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.services import feishu_ws


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动飞书长连接事件订阅客户端（官方推荐模式，无需公网 URL / 加密策略）
    if settings.FEISHU_APP_ID and settings.FEISHU_APP_SECRET:
        feishu_ws.start()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="ERP 智能采购管理系统：采购申请 → Agent 风控 → 人工审批（高风险）→ 飞书联动",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["健康检查"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME}
