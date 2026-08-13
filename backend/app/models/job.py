import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Enum as SAEnum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import get_settings
from app.db.base import Base, TimestampMixin, UpdatedAtMixin, UUIDPKMixin
from app.models.enums import JobStatus

settings = get_settings()


class Job(Base, UUIDPKMixin, TimestampMixin, UpdatedAtMixin):
    __tablename__ = "jobs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    employment_type: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # AI-derived job profile (section 9) - editable by the recruiter before save
    seniority: Mapped[str | None] = mapped_column(String(50))
    responsibilities: Mapped[list | None] = mapped_column(JSONB)
    min_experience_years: Mapped[float | None] = mapped_column(Float)
    preferred_experience_years: Mapped[float | None] = mapped_column(Float)
    education_requirements: Mapped[list | None] = mapped_column(JSONB)

    # Per-job configurable scoring weights (section 10) - must sum to 1.0
    weight_skills: Mapped[float] = mapped_column(Float, default=settings.DEFAULT_WEIGHT_SKILLS)
    weight_semantic: Mapped[float] = mapped_column(Float, default=settings.DEFAULT_WEIGHT_SEMANTIC)
    weight_experience: Mapped[float] = mapped_column(Float, default=settings.DEFAULT_WEIGHT_EXPERIENCE)
    weight_education: Mapped[float] = mapped_column(Float, default=settings.DEFAULT_WEIGHT_EDUCATION)
    weight_projects: Mapped[float] = mapped_column(Float, default=settings.DEFAULT_WEIGHT_PROJECTS)

    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus, name="job_status"), nullable=False, default=JobStatus.DRAFT
    )

    # Whole-JD embedding, used as a fallback / job-level semantic anchor
    embedding: Mapped[list[float] | None] = mapped_column(Vector(settings.EMBEDDING_DIMENSIONS))

    organization: Mapped["Organization"] = relationship(back_populates="jobs")
    requirements: Mapped[list["JobRequirement"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class JobRequirement(Base, UUIDPKMixin):
    """A single normalized skill/requirement extracted from a JD
    (section 9). `required=False` means 'preferred', not mandatory."""

    __tablename__ = "job_requirements"

    job_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_skill: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    importance: Mapped[float] = mapped_column(Float, default=1.0)  # 0.0-1.0
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    minimum_years: Mapped[float | None] = mapped_column(Float)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(settings.EMBEDDING_DIMENSIONS))

    job: Mapped["Job"] = relationship(back_populates="requirements")
