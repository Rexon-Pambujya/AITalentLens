"""
Semantic matching (section 12).

Uses pgvector cosine distance (`<=>` operator) against chunk-level resume
embeddings - never a single whole-resume embedding, per spec. Returns both
an aggregate score and the specific chunk(s) that drove it, since those
chunks become the "evidence" shown to the recruiter (section 72).
"""
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume, ResumeEmbedding


@dataclass
class SemanticMatchChunk:
    chunk_text: str
    similarity: float  # 0.0-1.0, cosine similarity (1 - cosine_distance)


@dataclass
class SemanticMatchResult:
    top_chunks: list[SemanticMatchChunk]
    average_top_k_similarity: float
    score: float  # 0-100


async def semantic_match_candidate(
    db: AsyncSession,
    *,
    candidate_id: UUID,
    query_embedding: list[float],
    top_k: int = 5,
) -> SemanticMatchResult:
    """Finds the candidate's `top_k` most-similar resume chunks to the
    query embedding (typically the JD's whole-description embedding) and
    scores based on their average similarity. Using top-k rather than a
    single best chunk keeps the score from being dominated by one lucky
    keyword-y sentence."""
    cosine_distance = ResumeEmbedding.embedding.cosine_distance(query_embedding)
    stmt = (
        select(ResumeEmbedding.chunk_text, cosine_distance.label("distance"))
        .join(Resume, Resume.id == ResumeEmbedding.resume_id)
        .where(Resume.candidate_id == candidate_id)
        .order_by(cosine_distance)
        .limit(top_k)
    )
    result = await db.execute(stmt)
    rows = result.all()

    if not rows:
        return SemanticMatchResult(top_chunks=[], average_top_k_similarity=0.0, score=0.0)

    chunks = [SemanticMatchChunk(chunk_text=row.chunk_text, similarity=round(1 - row.distance, 4)) for row in rows]
    avg_similarity = sum(c.similarity for c in chunks) / len(chunks)

    # Cosine similarity for real embedding models rarely exceeds ~0.9 even
    # for very strong matches, and mediocre matches often sit around
    # 0.3-0.5 - a raw 0-1 scale compressed straight to 0-100 would make
    # everything look like a poor match. Rescale so a similarity of ~0.35
    # (weak-but-relevant) lands near 50 and ~0.75+ lands near 100.
    rescaled = max(0.0, min(1.0, (avg_similarity - 0.15) / 0.65))
    score = round(rescaled * 100, 1)

    return SemanticMatchResult(top_chunks=chunks, average_top_k_similarity=round(avg_similarity, 4), score=score)


async def find_candidates_by_semantic_query(
    db: AsyncSession,
    *,
    organization_id: UUID,
    query_embedding: list[float],
    limit: int = 50,
) -> list[tuple[UUID, float, str]]:
    """Powers POST /search/candidates (section 18): semantic candidate
    search scoped to the caller's organization. Returns
    (candidate_id, similarity, best_matching_chunk_text) tuples, deduped to
    the single best-matching chunk per candidate, ranked by similarity."""
    from app.models.candidate import Candidate

    cosine_distance = ResumeEmbedding.embedding.cosine_distance(query_embedding)
    stmt = (
        select(
            Candidate.id,
            cosine_distance.label("distance"),
            ResumeEmbedding.chunk_text,
        )
        .join(Resume, Resume.candidate_id == Candidate.id)
        .join(ResumeEmbedding, ResumeEmbedding.resume_id == Resume.id)
        .where(Candidate.organization_id == organization_id)
        .order_by(cosine_distance)
        .limit(limit * 5)  # over-fetch, then dedupe to one best chunk per candidate below
    )
    result = await db.execute(stmt)

    seen: dict[UUID, tuple[float, str]] = {}
    for candidate_id, distance, chunk_text in result.all():
        similarity = round(1 - distance, 4)
        if candidate_id not in seen or similarity > seen[candidate_id][0]:
            seen[candidate_id] = (similarity, chunk_text)

    ranked = sorted(((cid, sim, text) for cid, (sim, text) in seen.items()), key=lambda t: t[1], reverse=True)
    return ranked[:limit]
