from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_llm_provider
from app.api.deps import get_db, require_recruiter_or_admin
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.schemas.matching import MatchRead, ScoreBreakdown
from app.services.audit_service import record_audit_log
from app.services.matching_service import calculate_match

router = APIRouter(tags=["matching"])


def _to_match_read(match) -> MatchRead:
    data = MatchRead.model_validate(match)
    data.score_breakdown = ScoreBreakdown(
        skills=match.skill_score,
        semantic=match.semantic_score,
        experience=match.experience_score,
        education=match.education_score,
        projects=match.project_score,
    )
    return data


@router.post("/candidates/{candidate_id}/match/{job_id}", response_model=MatchRead)
async def match_candidate_to_job(
    candidate_id: UUID,
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_recruiter_or_admin),
) -> MatchRead:
    """Runs the hybrid scoring engine for one candidate against one job and
    persists the result (section 34: recompute only on demand / when
    inputs change, not on every page load)."""
    llm = get_llm_provider()
    try:
        match = await calculate_match(
            db, llm, job_id=job_id, candidate_id=candidate_id, organization_id=current_user.organization_id
        )
    except ValueError as exc:
        raise NotFoundError(str(exc)) from exc

    await record_audit_log(
        db, user_id=current_user.id, action="MATCH_CALCULATED", resource_type="match", resource_id=match.id,
        metadata={"job_id": str(job_id), "candidate_id": str(candidate_id), "overall_score": match.overall_score},
    )
    await db.commit()
    return _to_match_read(match)
