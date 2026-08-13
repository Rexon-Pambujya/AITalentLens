from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_llm_provider
from app.api.deps import get_db, require_any_role
from app.core.exceptions import LLMUnavailableError
from app.matching.semantic_matcher import find_candidates_by_semantic_query
from app.models.candidate import Candidate
from app.models.user import User
from app.schemas.search import SemanticSearchRequest, SemanticSearchResponse, SemanticSearchResultItem

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/candidates", response_model=SemanticSearchResponse)
async def search_candidates(
    payload: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_role),
) -> SemanticSearchResponse:
    """Natural-language candidate search (section 18): 'Find candidates
    with experience building production RAG systems using Python and AWS.'
    Converts the query to an embedding and does a pgvector similarity
    search scoped to the caller's organization - never across tenants."""
    llm = get_llm_provider()
    try:
        query_embedding = (await llm.embed([payload.query]))[0]
    except LLMUnavailableError:
        return SemanticSearchResponse(
            query=payload.query, results=[], ai_available=False,
            message="Semantic search is temporarily unavailable (AI backend unreachable). "
            "Try the keyword filters instead.",
        )

    ranked = await find_candidates_by_semantic_query(
        db, organization_id=current_user.organization_id, query_embedding=query_embedding, limit=payload.limit
    )
    if not ranked:
        return SemanticSearchResponse(query=payload.query, results=[], ai_available=True)

    candidate_ids = [cid for cid, _, _ in ranked]
    result = await db.execute(select(Candidate).where(Candidate.id.in_(candidate_ids)))
    candidates_by_id = {c.id: c for c in result.scalars().all()}

    items = [
        SemanticSearchResultItem(
            candidate_id=cid,
            candidate_name=candidates_by_id[cid].name if cid in candidates_by_id else None,
            current_title=candidates_by_id[cid].current_title if cid in candidates_by_id else None,
            similarity=similarity,
            matching_evidence=chunk_text,
        )
        for cid, similarity, chunk_text in ranked
        if cid in candidates_by_id
    ]
    return SemanticSearchResponse(query=payload.query, results=items, ai_available=True)
