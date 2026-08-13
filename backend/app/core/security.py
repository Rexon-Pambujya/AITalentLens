"""
Password hashing and JWT issuance/verification.

Nothing in the request pipeline should ever trust a client-supplied role or
organization_id - identity is always re-derived from the verified JWT on the
server (see api/deps.py).
"""
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    *,
    subject: UUID,
    organization_id: UUID,
    role: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "org": str(organization_id),
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


class TokenPayload:
    __slots__ = ("user_id", "organization_id", "role")

    def __init__(self, user_id: UUID, organization_id: UUID, role: str):
        self.user_id = user_id
        self.organization_id = organization_id
        self.role = role


def decode_access_token(token: str) -> TokenPayload:
    """Raises jose.JWTError (caught by the caller) on any invalid/expired token."""
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    if payload.get("type") != "access":
        raise JWTError("Invalid token type")
    return TokenPayload(
        user_id=UUID(payload["sub"]),
        organization_id=UUID(payload["org"]),
        role=payload["role"],
    )
