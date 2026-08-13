from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.exceptions import AuthenticationError, DuplicateResourceError
from app.core.logging import get_logger
from app.core.security import create_access_token, hash_password, verify_password
from app.models.enums import UserRole
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import Token, UserLogin, UserRead, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)) -> Token:
    """Creates a brand-new organization plus its first user, who becomes
    ADMIN. Subsequent teammates are invited via POST /users (not shown in
    this phase) rather than through this endpoint."""
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise DuplicateResourceError("An account with this email already exists")

    organization = Organization(name=payload.organization_name)
    db.add(organization)
    await db.flush()  # populate organization.id without committing yet

    user = User(
        organization_id=organization.id,
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        role=UserRole.ADMIN,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("user_registered", user_id=str(user.id), organization_id=str(organization.id))

    token = create_access_token(
        subject=user.id, organization_id=user.organization_id, role=user.role.value
    )
    return Token(access_token=token, user=UserRead.model_validate(user))


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)) -> Token:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise AuthenticationError("Invalid email or password")
    if not user.is_active:
        raise AuthenticationError("This account has been deactivated")

    logger.info("user_login", user_id=str(user.id))

    token = create_access_token(
        subject=user.id, organization_id=user.organization_id, role=user.role.value
    )
    return Token(access_token=token, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
