from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_llm_provider
from app.api.deps import get_current_user, get_db, require_recruiter_or_admin
from app.extraction.jd_extractor import extract_job_profile
from app.extraction.schemas import JobProfile
from app.models.enums import JobStatus
from app.models.user import User
from app.schemas.job import JobAnalyzeRequest, JobCreate, JobRead, JobUpdate
from app.services import job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_recruiter_or_admin),
) -> JobRead:
    job = await job_service.create_job(
        db, organization_id=current_user.organization_id, user_id=current_user.id, payload=payload
    )
    return JobRead.model_validate(job)


@router.get("", response_model=dict)
async def list_jobs(
    status_filter: JobStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    jobs, total = await job_service.list_jobs(
        db,
        organization_id=current_user.organization_id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [JobRead.model_validate(j) for j in jobs],
    }


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobRead:
    job = await job_service.get_job(db, organization_id=current_user.organization_id, job_id=job_id)
    return JobRead.model_validate(job)


@router.patch("/{job_id}", response_model=JobRead)
async def update_job(
    job_id: UUID,
    payload: JobUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_recruiter_or_admin),
) -> JobRead:
    job = await job_service.update_job(
        db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        job_id=job_id,
        payload=payload,
    )
    return JobRead.model_validate(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_recruiter_or_admin),
) -> None:
    """DELETE archives rather than hard-deletes (see job_service.archive_job)."""
    await job_service.archive_job(
        db, organization_id=current_user.organization_id, user_id=current_user.id, job_id=job_id
    )


@router.post("/{job_id}/analyze", response_model=JobProfile)
async def analyze_job_description(
    job_id: UUID,
    payload: JobAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_recruiter_or_admin),
) -> JobProfile:
    """Section 9/45: runs JD extraction and returns the proposed structured
    profile WITHOUT saving it - the recruiter reviews/edits in the UI, then
    calls PATCH /jobs/{id} to actually persist their (possibly edited)
    choices. This endpoint never silently mutates the Job row."""
    job = await job_service.get_job(db, organization_id=current_user.organization_id, job_id=job_id)
    description = payload.description or job.description

    llm = get_llm_provider()
    profile = await extract_job_profile(llm, jd_text=description)
    if profile is None:
        # Graceful degradation (section 62) - return an empty profile with
        # an explanatory message rather than a 503, so the UI can still
        # show the "AI analysis temporarily unavailable" state (section 62)
        # and let the recruiter fill the form in manually.
        return JobProfile(title=job.title, ambiguous_requirements=["AI analysis is temporarily unavailable - please fill in requirements manually."])
    return profile
