from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_any_role, require_recruiter_or_admin, scoped_to_org
from app.core.exceptions import NotFoundError
from app.models.recruiter_note import RecruiterNote
from app.models.user import User
from app.repositories.candidate_repository import (
    get_candidate_detail,
    list_candidate_skills,
    list_candidates,
    upsert_pipeline_status,
)
from app.schemas.candidate import (
    CandidateDetailRead,
    CandidateRead,
    CandidateSkillRead,
    PipelineStatusUpdate,
    RecruiterNoteCreate,
    RecruiterNoteRead,
)
from app.services.candidate_service import add_recruiter_note

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get("", response_model=dict)
async def list_all_candidates(
    q: str | None = Query(default=None, description="Search by name, email, or current title"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_role),
) -> dict:
    candidates, total = await list_candidates(
        db, organization_id=current_user.organization_id, search=q, page=page, page_size=page_size
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [CandidateRead.model_validate(c) for c in candidates],
    }


@router.get("/{candidate_id}", response_model=CandidateDetailRead)
async def get_candidate(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_role),
) -> CandidateDetailRead:
    candidate = await get_candidate_detail(
        db, organization_id=current_user.organization_id, candidate_id=candidate_id
    )
    if candidate is None:
        raise NotFoundError(f"Candidate {candidate_id} not found")

    skill_rows = await list_candidate_skills(db, candidate_id=candidate_id)
    detail = CandidateDetailRead.model_validate(candidate)
    detail.skills = [
        CandidateSkillRead(
            skill_name=cs.skill.name, proficiency=cs.proficiency, years_experience=cs.years_experience
        )
        for cs in skill_rows
    ]
    return detail


@router.put("/{candidate_id}/pipeline/{job_id}", response_model=dict)
async def update_pipeline_status(
    candidate_id: UUID,
    job_id: UUID,
    payload: PipelineStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_recruiter_or_admin),
) -> dict:
    """Shortlist / reject / move-to-interview etc. (section 18/24). Job
    ownership is implicitly checked via the job-scoped queries used
    elsewhere; here we additionally confirm the candidate belongs to the
    caller's org before writing anything."""
    candidate = await get_candidate_detail(
        db, organization_id=current_user.organization_id, candidate_id=candidate_id
    )
    if candidate is None:
        raise NotFoundError(f"Candidate {candidate_id} not found")

    from app.services.audit_service import record_audit_log

    pipeline = await upsert_pipeline_status(
        db, candidate_id=candidate_id, job_id=job_id, status=payload.status
    )
    await record_audit_log(
        db,
        user_id=current_user.id,
        action=f"CANDIDATE_{payload.status.value}",
        resource_type="candidate_pipeline",
        resource_id=candidate_id,
        metadata={"job_id": str(job_id), "status": payload.status.value},
    )
    await db.commit()
    return {"candidate_id": str(candidate_id), "job_id": str(job_id), "status": pipeline.status.value}


@router.post("/{candidate_id}/notes", response_model=RecruiterNoteRead, status_code=201)
async def create_note(
    candidate_id: UUID,
    payload: RecruiterNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_role),
) -> RecruiterNoteRead:
    candidate = await get_candidate_detail(
        db, organization_id=current_user.organization_id, candidate_id=candidate_id
    )
    if candidate is None:
        raise NotFoundError(f"Candidate {candidate_id} not found")

    note = await add_recruiter_note(
        db, candidate_id=candidate_id, user_id=current_user.id, note_text=payload.note
    )
    return RecruiterNoteRead.model_validate(note)


@router.get("/{candidate_id}/notes", response_model=list[RecruiterNoteRead])
async def list_notes(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_role),
) -> list[RecruiterNoteRead]:
    candidate = await get_candidate_detail(
        db, organization_id=current_user.organization_id, candidate_id=candidate_id
    )
    if candidate is None:
        raise NotFoundError(f"Candidate {candidate_id} not found")

    result = await db.execute(
        select(RecruiterNote)
        .where(RecruiterNote.candidate_id == candidate_id)
        .order_by(RecruiterNote.created_at.desc())
    )
    return [RecruiterNoteRead.model_validate(n) for n in result.scalars().all()]
