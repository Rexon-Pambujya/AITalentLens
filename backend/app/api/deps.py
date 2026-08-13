"""
Shared FastAPI dependencies.

Two rules enforced everywhere in this module, per spec sections 30/31:

1. Authorization is decided on the SERVER from the verified JWT claims -
   never from a client-supplied header/body field.
2. Every query that touches organization-scoped data must filter by the
   organization_id taken from the token, so one tenant can never read
   another tenant's rows (see `require_roles` and the pattern used by
   services built on top of `get_current_user`).
"""
from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if token is None:
        raise AuthenticationError("Not authenticated")
    try:
        payload = decode_access_token(token)
    except JWTError as exc:
        raise AuthenticationError("Invalid or expired token") from exc

    result = await db.execute(select(User).where(User.id == payload.user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise AuthenticationError("User not found or inactive")
    # Defensive check: the org_id embedded in the token must still match the
    # user's current row (covers the rare case of an org transfer).
    if user.organization_id != payload.organization_id:
        raise AuthenticationError("Token organization mismatch")
    return user


def require_roles(*allowed_roles: UserRole) -> Callable:
    """Usage: `current_user: User = Depends(require_roles(UserRole.ADMIN))`.

    Enforced server-side per section 30: "Never rely only on frontend
    authorization."
    """

    async def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise AuthorizationError(
                f"Role '{current_user.role.value}' is not permitted to perform this action"
            )
        return current_user

    return _dependency


# Convenience role bundles matching section 30's permission matrix
require_admin = require_roles(UserRole.ADMIN)
require_recruiter_or_admin = require_roles(UserRole.ADMIN, UserRole.RECRUITER)
require_any_role = require_roles(UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER)


def scoped_to_org(current_user: User, resource_org_id: UUID) -> None:
    """Call this before returning/mutating any organization-scoped row.
    Raises rather than silently filtering, so a cross-tenant attempt is
    audit-logged as an authorization failure, not a quiet 404."""
    if current_user.organization_id != resource_org_id:
        from app.core.exceptions import CrossTenantAccessError

        raise CrossTenantAccessError("Resource does not belong to your organization")
