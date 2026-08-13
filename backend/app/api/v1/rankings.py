from enum import Enum
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_llm_provider
from app.api.deps import get_current_user, get_db, require_any_role, require_recruiter_or_admin
from app.core.exceptions import NotFoundError
from app.models.candidate import Candidate
from app.models.candidate_pipeline import CandidatePipeline
from app.models.job import Job
from app.models.match import Match
from app.models.user import User
from app.schemas.matching import RankingEntry
from app.services.job_service import get_job
from app.services.matching_service import calculate_match

router = APIRouter(prefix="/jobs", tags=["rankings"])


class SortOption(str, Enum):
    OVERALL_SCORE = "overall_score"
    SKILL_MATCH = "skill_match"
    EXPERIENCE = "experience"
    SEMANTIC = "semantic"
    RECENTLY_ADDED = "recently_added"


_SORT_COLUMN = {
    SortOption.OVERALL_SCORE: Match.overall_score,
    SortOption.SKILL_MATCH: Match.skill_score,
    SortOption.EXPERIENCE: Match.experience_score,
    SortOption.SEMANTIC: Match.semantic_score,
    SortOption.RECENTLY_ADDED: Match.created_at,
}


@router.get("/{job_id}/ranking", response_model=list[RankingEntry])
async def get_job_ranking(
    job_id: UUID,
    sort_by: SortOption = Query(default=SortOption.OVERALL_SCORE),
    min_score: float | None = Query(default=None, ge=0, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_role),
) -> list[RankingEntry]:
    """Section 17: ranked candidate list for a job, with sort options and
    score filtering. Reads persisted Match rows only - does NOT trigger
    recalculation (use POST /jobs/{id}/recalculate for that)."""
    await get_job(db, organization_id=current_user.organization_id, job_id=job_id)  # 404s + tenant check

    query = (
        select(Match, Candidate, CandidatePipeline.status)
        .join(Candidate, Candidate.id == Match.candidate_id)
        .outerjoin(
            CandidatePipeline,
            (CandidatePipeline.candidate_id == Match.candidate_id) & (CandidatePipeline.job_id == job_id),
        )
        .where(Match.job_id == job_id)
    )
    if min_score is not None:
        query = query.where(Match.overall_score >= min_score)

    sort_column = _SORT_COLUMN[sort_by]
    query = query.order_by(sort_column.desc())

    result = await db.execute(query)
    rows = result.all()

    return [
        RankingEntry(
            rank=idx + 1,
            candidate_id=match.candidate_id,
            candidate_name=candidate.name,
            current_title=candidate.current_title,
            overall_score=match.overall_score,
            skill_score=match.skill_score,
            experience_score=match.experience_score,
            semantic_score=match.semantic_score,
            recommendation=match.recommendation,
            missing_skills=match.missing_skills,
            pipeline_status=pipeline_status.value if pipeline_status else None,
        )
        for idx, (match, candidate, pipeline_status) in enumerate(rows)
    ]


@router.get("/{job_id}/candidates", response_model=list[RankingEntry])
async def get_job_candidates(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_role),
) -> list[RankingEntry]:
    """Alias of /ranking with default sort - matches spec's separate
    GET /jobs/{id}/candidates endpoint (section 37)."""
    return await get_job_ranking(job_id, SortOption.OVERALL_SCORE, None, db, current_user)


@router.post("/{job_id}/recalculate", response_model=dict)
async def recalculate_job_matches(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_recruiter_or_admin),
) -> dict:
    """Recomputes matches for every candidate who has ever been matched
    against this job, or who has at least one resume in the org. Section
    34: only recompute on demand (scoring config change, model change,
    etc.) - never silently on every page view."""
    await get_job(db, organization_id=current_user.organization_id, job_id=job_id)

    result = await db.execute(
        select(Candidate.id).where(Candidate.organization_id == current_user.organization_id)
    )
    candidate_ids = [row[0] for row in result.all()]

    llm = get_llm_provider()
    recalculated = 0
    failed = 0
    for candidate_id in candidate_ids:
        try:
            await calculate_match(
                db, llm, job_id=job_id, candidate_id=candidate_id, organization_id=current_user.organization_id
            )
            recalculated += 1
        except Exception:  # noqa: BLE001 - one bad candidate shouldn't abort the whole batch
            failed += 1

    return {"job_id": str(job_id), "candidates_recalculated": recalculated, "failed": failed}
