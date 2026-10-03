"""认证与组织 API：登录（JWT）、当前用户、员工列表。

登录说明：员工已设置 password_hash 时强制校验密码；演示期未设密码的员工
可直接登录（后续接入正式账号体系后收紧）。
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import DbSession
from app.core.security import create_access_token, decode_token, verify_password
from app.models.org import Employee
from app.schemas.org import EmployeeOut

router = APIRouter()
org_router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


class LoginRequest(BaseModel):
    employee_no: str
    password: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    employee: EmployeeOut


async def _get_employee_by_no(db, employee_no: str) -> Optional[Employee]:
    result = await db.execute(select(Employee).where(Employee.employee_no == employee_no))
    return result.scalar_one_or_none()


async def _resolve_token(db, token: Optional[str]) -> Optional[Employee]:
    """解析 Bearer token；无效或员工不可用时返回 None。"""
    if not token:
        return None
    employee_no = decode_token(token)
    if not employee_no:
        return None
    emp = await _get_employee_by_no(db, employee_no)
    return emp if emp and emp.status == "active" else None


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, db: DbSession):
    """登录：工号 + 密码（已设置密码的必须校验；未设置的演示期直接放行）。"""
    emp = await _get_employee_by_no(db, payload.employee_no)
    if emp is None or emp.status != "active":
        raise HTTPException(status_code=401, detail="工号不存在或账号不可用")
    if emp.password_hash:
        if not payload.password or not verify_password(payload.password, emp.password_hash):
            raise HTTPException(status_code=401, detail="密码错误")
    token = create_access_token(subject=str(emp.employee_no))
    return LoginResponse(access_token=token, employee=EmployeeOut.model_validate(emp))


@router.get("/me", response_model=EmployeeOut)
async def me(db: DbSession, token: Optional[str] = Depends(oauth2_scheme)):
    """当前登录用户信息。"""
    emp = await _resolve_token(db, token)
    if emp is None:
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    return emp


@org_router.get("/employees", response_model=list[EmployeeOut])
async def list_employees(db: DbSession):
    """员工列表（登录/申请人选择用），仅返回启用状态的员工。"""
    result = await db.execute(
        select(Employee).where(Employee.status == "active").order_by(Employee.id)
    )
    return result.scalars().all()
