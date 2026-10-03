"""FastAPI 公共依赖。"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.org import Employee

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbSession,
    token: Annotated[str | None, Depends(oauth2_scheme)] = None,
) -> Employee | None:
    """当前登录用户：解析 JWT 返回员工；无 token 或无效时返回 None（接口自行决定是否放宽）。"""
    if not token:
        return None
    from app.core.security import decode_token

    employee_no = decode_token(token)
    if not employee_no:
        return None
    result = await db.execute(select(Employee).where(Employee.employee_no == employee_no))
    emp = result.scalar_one_or_none()
    if emp is None or emp.status != "active":
        return None
    return emp


async def get_admin_user(current_user: Annotated[Employee | None, Depends(get_current_user)]) -> Employee:
    if current_user is None or current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return current_user
