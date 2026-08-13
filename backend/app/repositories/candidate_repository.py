import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.candidate import Candidate
from app.models.candidate_pipeline import CandidatePipeline
from app.models.skill import CandidateSkill


async def get_candidate_detail(
    db: AsyncSession, *, organization_id: uuid.UUID, candidate_id: uuid.UUID
) -> Candidate | None:
    result = await db.execute(
        select(Candidate)
        .options(
            selectinload(Candidate.experiences),
            selectinload(Candidate.educations),
            selectinload(Candidate.certifications),
            selectinload(Candidate.projects),
        )
        .where(Candidate.id == candidate_id, Candidate.organization_id == organization_id)
    )
    return result.scalars().first()


async def list_candidate_skills(db: AsyncSession, *, candidate_id: uuid.UUID) -> list[CandidateSkill]:
    result = await db.execute(
        select(CandidateSkill)
        .options(selectinload(CandidateSkill.skill))
        .where(CandidateSkill.candidate_id == candidate_id)
    )
    return list(result.scalars().all())


async def list_candidates(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Candidate], int]:
    query = select(Candidate).where(Candidate.organization_id == organization_id)
    if search:
        like = f"%{search.lower()}%"
        from sqlalchemy import func, or_

        query = query.where(
            or_(
                func.lower(Candidate.name).like(like),
                func.lower(Candidate.email).like(like),
                func.lower(Candidate.current_title).like(like),
            )
        )

    count_result = await db.execute(query)
    total = len(count_result.scalars().all())

    query = query.order_by(Candidate.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_pipeline_status(
    db: AsyncSession, *, candidate_id: uuid.UUID, job_id: uuid.UUID
) -> CandidatePipeline | None:
    result = await db.execute(
        select(CandidatePipeline).where(
            CandidatePipeline.candidate_id == candidate_id, CandidatePipeline.job_id == job_id
        )
    )
    return result.scalars().first()


async def upsert_pipeline_status(
    db: AsyncSession, *, candidate_id: uuid.UUID, job_id: uuid.UUID, status
) -> CandidatePipeline:
    pipeline = await get_pipeline_status(db, candidate_id=candidate_id, job_id=job_id)
    if pipeline is None:
        pipeline = CandidatePipeline(candidate_id=candidate_id, job_id=job_id, status=status)
        db.add(pipeline)
    else:
        pipeline.status = status
    await db.flush()
    return pipeline
