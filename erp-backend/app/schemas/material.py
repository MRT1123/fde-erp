"""物料 Schemas。"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MaterialCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=150)
    category: str = Field(min_length=1, max_length=50)
    spec: Optional[str] = None
    unit: str = "件"
    default_price: Optional[float] = None


class MaterialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    category: str
    spec: Optional[str]
    unit: str
    default_price: Optional[float]
    status: str


class MaterialUpdate(BaseModel):
    """物料更新：仅需传入要修改的字段。"""

    name: Optional[str] = None
    category: Optional[str] = None
    spec: Optional[str] = None
    unit: Optional[str] = None
    default_price: Optional[float] = None
    status: Optional[str] = None
