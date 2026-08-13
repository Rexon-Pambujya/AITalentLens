from uuid import UUID

from pydantic import BaseModel


class SemanticSearchRequest(BaseModel):
    query: str
    limit: int = 20


class SemanticSearchResultItem(BaseModel):
    candidate_id: UUID
    candidate_name: str | None
    current_title: str | None
    similarity: float
    matching_evidence: str


class SemanticSearchResponse(BaseModel):
    query: str
    results: list[SemanticSearchResultItem]
    ai_available: bool
    message: str | None = None
