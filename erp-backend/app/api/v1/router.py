"""API v1 路由汇总。"""
from fastapi import APIRouter

from app.api.v1 import (
    approvals,
    auth,
    budget,
    dashboard,
    inventory,
    materials,
    purchase,
    purchase_orders,
    suppliers,
    webhooks,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(auth.org_router, tags=["组织"])
api_router.include_router(purchase.router, prefix="/purchase-requests", tags=["采购申请"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["审批"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["供应商"])
api_router.include_router(materials.router, prefix="/materials", tags=["物料"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["库存"])
api_router.include_router(budget.router, prefix="/budget", tags=["预算管控"])
api_router.include_router(purchase_orders.router, prefix="/purchase-orders", tags=["采购订单"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["数据看板"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhook"])
