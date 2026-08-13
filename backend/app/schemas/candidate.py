from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import PipelineStatus


class ExperienceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    company: str | None
    title: str | None
    start_date: date | None
    end_date: date | None
    description: str | None
    years: float | None


class EducationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution: str | None
    degree: str | None
    field: str | None
    start_year: int | None
    end_year: int | None


class CertificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    issuer: str | None
    issue_date: date | None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: str | None
    technologies: list | None


class CandidateSkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    skill_name: str
    proficiency: str | None
    years_experience: float | None


class CandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str | None
    email: str | None
    phone: str | None
    location: str | None
    linkedin_url: str | None
    github_url: str | None
    portfolio_url: str | None
    total_years_experience: float | None
    current_title: str | None
    current_company: str | None
    created_at: datetime
    updated_at: datetime


class CandidateDetailRead(CandidateRead):
    experiences: list[ExperienceRead] = []
    educations: list[EducationRead] = []
    certifications: list[CertificationRead] = []
    projects: list[ProjectRead] = []
    skills: list[CandidateSkillRead] = []


class PipelineStatusUpdate(BaseModel):
    status: PipelineStatus


class RecruiterNoteCreate(BaseModel):
    note: str


class RecruiterNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    note: str
    user_id: UUID | None
    created_at: datetime
