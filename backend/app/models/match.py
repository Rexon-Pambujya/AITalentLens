import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import RecommendationLabel


class Match(Base, UUIDPKMixin, TimestampMixin):
    """A persisted scoring result for one (job, candidate) pair.

    Persisting this (rather than recomputing on every page view) is
    deliberate - see spec section 34, LLM Cost Control: only recompute when
    the resume, JD, scoring config, or model/prompt version changes.
    `model_name` / `scoring_version` make every result reproducible and
    auditable (section 35).
    """

    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("job_id", "candidate_id", name="uq_match_job_candidate"),)

    job_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )

    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    skill_score: Mapped[float] = mapped_column(Float, nullable=False)
    semantic_score: Mapped[float] = mapped_column(Float, nullable=False)
    experience_score: Mapped[float] = mapped_column(Float, nullable=False)
    education_score: Mapped[float] = mapped_column(Float, nullable=False)
    certification_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    project_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    matched_skills: Mapped[list] = mapped_column(JSONB, default=list)
    missing_skills: Mapped[list] = mapped_column(JSONB, default=list)
    partial_skills: Mapped[list] = mapped_column(JSONB, default=list)
    strengths: Mapped[list] = mapped_column(JSONB, default=list)
    improvements: Mapped[list] = mapped_column(JSONB, default=list)
    interview_focus: Mapped[list] = mapped_column(JSONB, default=list)
    evidence: Mapped[list] = mapped_column(JSONB, default=list)

    recommendation: Mapped[RecommendationLabel] = mapped_column(
        SAEnum(RecommendationLabel, name="recommendation_label"), nullable=False
    )
    reasoning: Mapped[dict] = mapped_column(JSONB, default=dict)
    # LLM-authored "why this candidate" narrative (section 26), generated
    # strictly from the deterministic facts above - see
    # app/matching/llm_explanation.py. Null when AI was unavailable; the
    # deterministic strengths/improvements/reasoning above are always
    # present regardless, so the UI never has nothing to show.
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(20), nullable=False)

    job: Mapped["Job"] = relationship()
    candidate: Mapped["Candidate"] = relationship()
