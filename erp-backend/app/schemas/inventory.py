"""库存相关 Schemas。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class InventoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    material_id: int
    warehouse: str
    quantity: float
    reserved_quantity: float
    safety_stock: Optional[float]
    updated_at: datetime


class StockMovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    material_id: int
    movement_type: str
    quantity: float
    reference_type: Optional[str]
    reference_id: Optional[int]
    remark: Optional[str]
    created_at: datetime


class StockChangeIn(BaseModel):
    """库存变动：in 入库 / out 出库 / adjust 盘盈盘亏。"""

    material_id: int
    movement_type: str  # in / out / adjust
    quantity: float  # 正数；out 表示从可用库存扣减
    warehouse: str = "default"
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    remark: Optional[str] = None
