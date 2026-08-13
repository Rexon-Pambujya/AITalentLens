from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def record_audit_log(
    db: AsyncSession,
    *,
    user_id: UUID | None,
    action: str,
    resource_type: str,
    resource_id: UUID | None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Appends an audit row in the same transaction as the caller's other
    writes (no separate commit here - the caller commits once). See
    spec section 64."""
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            log_metadata=metadata or {},
        )
    )
