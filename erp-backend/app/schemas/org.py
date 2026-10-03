"""组织架构 Schemas。"""
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    parent_id: Optional[int]
    manager_id: Optional[int]
    budget_limit: Optional[float]


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_no: str
    name: str
    email: Optional[str]
    department_id: Optional[int]
    role: str
    approval_limit: Optional[float]
    status: str
