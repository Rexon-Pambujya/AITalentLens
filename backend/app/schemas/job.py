from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import JobStatus


class JobRequirementCreate(BaseModel):
    skill: str
    importance: float = Field(default=1.0, ge=0.0, le=1.0)
    required: bool = True
    minimum_years: float | None = None


class JobRequirementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    skill: str
    normalized_skill: str
    importance: float
    required: bool
    minimum_years: float | None


class ScoringWeights(BaseModel):
    skills: float = 0.40
    semantic: float = 0.20
    experience: float = 0.20
    education: float = 0.10
    projects: float = 0.10

    @field_validator("projects")
    @classmethod
    def _weights_sum_to_one(cls, v, info):
        total = v + sum(info.data.get(k, 0) for k in ("skills", "semantic", "experience", "education"))
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Scoring weights must sum to 1.0, got {total}")
        return v


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    department: str | None = None
    location: str | None = None
    employment_type: str | None = None
    description: str = Field(min_length=1)
    requirements: list[JobRequirementCreate] = Field(default_factory=list)
    scoring_weights: ScoringWeights | None = None


class JobUpdate(BaseModel):
    title: str | None = None
    department: str | None = None
    location: str | None = None
    employment_type: str | None = None
    description: str | None = None
    status: JobStatus | None = None
    seniority: str | None = None
    min_experience_years: float | None = None
    preferred_experience_years: float | None = None
    scoring_weights: ScoringWeights | None = None
    # Replaces the job's entire requirements list when provided (section 45:
    # recruiter reviews/edits the AI-drafted profile, then this persists
    # their final choices). None means "leave requirements unchanged".
    requirements: list[JobRequirementCreate] | None = None


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    title: str
    department: str | None
    location: str | None
    employment_type: str | None
    description: str
    status: JobStatus
    seniority: str | None
    min_experience_years: float | None
    preferred_experience_years: float | None
    weight_skills: float
    weight_semantic: float
    weight_experience: float
    weight_education: float
    weight_projects: float
    requirements: list[JobRequirementRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class JobAnalyzeRequest(BaseModel):
    """Input to POST /jobs/{id}/analyze - re-runs JD extraction (section 9)
    against the current description, without saving until the recruiter
    confirms (section 45: AI should assist, not silently decide)."""

    description: str | None = None  # if omitted, re-analyzes the stored description
