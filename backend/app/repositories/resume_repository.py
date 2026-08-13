import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate
from app.models.resume import Resume


async def find_resume_by_hash(
    db: AsyncSession, *, organization_id: uuid.UUID, file_hash: str
) -> Resume | None:
    """Exact-duplicate lookup scoped to the organization (section 20)."""
    result = await db.execute(
        select(Resume)
        .join(Candidate, Candidate.id == Resume.candidate_id)
        .where(Candidate.organization_id == organization_id, Resume.file_hash == file_hash)
    )
    return result.scalars().first()


async def find_candidate_by_email(
    db: AsyncSession, *, organization_id: uuid.UUID, email: str
) -> Candidate | None:
    result = await db.execute(
        select(Candidate).where(Candidate.organization_id == organization_id, Candidate.email == email)
    )
    return result.scalars().first()


async def get_resume(db: AsyncSession, *, resume_id: uuid.UUID) -> Resume | None:
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    return result.scalars().first()
