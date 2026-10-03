"""审计日志服务。"""
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def record_audit(
    db: AsyncSession,
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    actor_type: str = "user",
    user_id: Optional[int] = None,
    detail: Optional[dict[str, Any]] = None,
    ip: Optional[str] = None,
) -> None:
    """记录一条审计日志。"""
    db.add(
        AuditLog(
            user_id=user_id,
            actor_type=actor_type,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            detail=detail,
            ip=ip,
        )
    )
    await db.commit()
