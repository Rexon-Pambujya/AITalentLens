from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import RecommendationLabel


class ScoreBreakdown(BaseModel):
    skills: float
    semantic: float
    experience: float
    education: float
    projects: float


class MatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: UUID
    job_id: UUID
    candidate_id: UUID
    overall_score: float
    recommendation: RecommendationLabel
    score_breakdown: ScoreBreakdown | None = None
    matched_skills: list
    missing_skills: list
    partial_skills: list
    strengths: list
    improvements: list
    interview_focus: list
    evidence: list
    reasoning: dict
    summary: str | None = None
    model_name: str
    embedding_model: str
    prompt_version: str
    scoring_version: str
    created_at: datetime


class RankingEntry(BaseModel):
    rank: int
    candidate_id: UUID
    candidate_name: str | None
    current_title: str | None
    overall_score: float
    skill_score: float
    experience_score: float
    semantic_score: float
    recommendation: RecommendationLabel
    missing_skills: list
    pipeline_status: str | None = None
