"""通用响应结构。"""
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Message(BaseModel):
    message: str


class Page(BaseModel):
    page: int = 1
    page_size: int = 20
    total: int = 0


class PageResult(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int
