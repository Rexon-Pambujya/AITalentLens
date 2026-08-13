"""
Chunk-level embedding generation (section 12). Degrades gracefully: if the
LLM/embedding backend is unreachable, returns an empty list rather than
raising, so the resume pipeline can still complete with extraction-only
results (section 62).
"""
from app.ai.base import LLMProvider
from app.core.exceptions import LLMUnavailableError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Keep batches modest so a single failed request doesn't waste a huge
# amount of already-computed work, and to stay under typical provider
# per-request batch limits.
EMBEDDING_BATCH_SIZE = 32


async def embed_chunks(llm: LLMProvider, chunks: list[str]) -> list[list[float]] | None:
    if not chunks:
        return []
    try:
        all_vectors: list[list[float]] = []
        for i in range(0, len(chunks), EMBEDDING_BATCH_SIZE):
            batch = chunks[i : i + EMBEDDING_BATCH_SIZE]
            vectors = await llm.embed(batch)
            all_vectors.extend(vectors)
        return all_vectors
    except LLMUnavailableError as exc:
        logger.warning("embedding_generation_unavailable", error=str(exc))
        return None
