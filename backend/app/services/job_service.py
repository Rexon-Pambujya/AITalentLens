"""
Job service.

Business logic lives here, not in the API layer (section 58: repository/
service separation). Every method takes `organization_id` explicitly and
filters on it - there is no code path in this service that can return a
row belonging to a different organization.
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.enums import JobStatus
from app.models.job import Job, JobRequirement
from app.schemas.job import JobCreate, JobUpdate
from app.services.audit_service import record_audit_log
from app.utils.normalization import normalize_skill_name, normalize_text


async def create_job(
    db: AsyncSession, *, organization_id: UUID, user_id: UUID, payload: JobCreate
) -> Job:
    job = Job(
        organization_id=organization_id,
        title=payload.title,
        department=payload.department,
        location=payload.location,
        employment_type=payload.employment_type,
        description=payload.description,
        status=JobStatus.DRAFT,
    )
    if payload.scoring_weights:
        job.weight_skills = payload.scoring_weights.skills
        job.weight_semantic = payload.scoring_weights.semantic
        job.weight_experience = payload.scoring_weights.experience
        job.weight_education = payload.scoring_weights.education
        job.weight_projects = payload.scoring_weights.projects

    for req in payload.requirements:
        canonical = normalize_skill_name(req.skill)
        job.requirements.append(
            JobRequirement(
                skill=canonical,
                normalized_skill=normalize_text(canonical),
                importance=req.importance,
                required=req.required,
                minimum_years=req.minimum_years,
            )
        )

    db.add(job)
    await db.flush()
    await record_audit_log(
        db, user_id=user_id, action="JOB_CREATED", resource_type="job", resource_id=job.id
    )
    await db.commit()
    return await get_job(db, organization_id=organization_id, job_id=job.id)


async def get_job(db: AsyncSession, *, organization_id: UUID, job_id: UUID) -> Job:
    result = await db.execute(
        select(Job)
        .options(selectinload(Job.requirements))
        .where(Job.id == job_id, Job.organization_id == organization_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise NotFoundError(f"Job {job_id} not found")
    return job


async def list_jobs(
    db: AsyncSession,
    *,
    organization_id: UUID,
    status_filter: JobStatus | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Job], int]:
    query = select(Job).options(selectinload(Job.requirements)).where(
        Job.organization_id == organization_id
    )
    if status_filter:
        query = query.where(Job.status == status_filter)

    count_result = await db.execute(query)
    all_rows = count_result.scalars().all()
    total = len(all_rows)

    query = query.order_by(Job.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def update_job(
    db: AsyncSession, *, organization_id: UUID, user_id: UUID, job_id: UUID, payload: JobUpdate
) -> Job:
    job = await get_job(db, organization_id=organization_id, job_id=job_id)

    update_data = payload.model_dump(exclude_unset=True, exclude={"scoring_weights", "requirements"})
    for field, value in update_data.items():
        setattr(job, field, value)

    if payload.scoring_weights:
        job.weight_skills = payload.scoring_weights.skills
        job.weight_semantic = payload.scoring_weights.semantic
        job.weight_experience = payload.scoring_weights.experience
        job.weight_education = payload.scoring_weights.education
        job.weight_projects = payload.scoring_weights.projects

    if payload.requirements is not None:
        job.requirements.clear()
        for req in payload.requirements:
            canonical = normalize_skill_name(req.skill)
            job.requirements.append(
                JobRequirement(
                    skill=canonical,
                    normalized_skill=normalize_text(canonical),
                    importance=req.importance,
                    required=req.required,
                    minimum_years=req.minimum_years,
                )
            )

    await record_audit_log(
        db, user_id=user_id, action="JOB_UPDATED", resource_type="job", resource_id=job.id,
        metadata={"fields": list(update_data.keys())},
    )
    await db.commit()
    return await get_job(db, organization_id=organization_id, job_id=job_id)


async def archive_job(db: AsyncSession, *, organization_id: UUID, user_id: UUID, job_id: UUID) -> None:
    """Jobs are archived, not hard-deleted, so historical matches/analytics
    remain intact (soft delete, matches spec's emphasis on auditability)."""
    job = await get_job(db, organization_id=organization_id, job_id=job_id)
    job.status = JobStatus.ARCHIVED
    await record_audit_log(
        db, user_id=user_id, action="JOB_ARCHIVED", resource_type="job", resource_id=job.id
    )
    await db.commit()
