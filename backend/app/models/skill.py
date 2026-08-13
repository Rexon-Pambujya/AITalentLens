import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin
from app.models.enums import SkillSource


class Skill(Base, UUIDPKMixin):
    """Canonical skill taxonomy entry (section 9: 'PyTorch'/'pytorch'/'torch'
    all normalize to a single canonical Skill row). Populated by a seed
    script and grown incrementally as new skills are encountered."""

    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    category: Mapped[str | None] = mapped_column(String(100))  # e.g. "ml_ai", "cloud", "language"


class CandidateSkill(Base):
    """Association object (not a plain secondary table) because we need to
    carry proficiency/years/source per (candidate, skill) pair."""

    __tablename__ = "candidate_skills"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    proficiency: Mapped[str | None] = mapped_column(String(50))  # e.g. beginner/intermediate/expert
    years_experience: Mapped[float | None] = mapped_column(Float)
    source: Mapped[SkillSource] = mapped_column(
        SAEnum(SkillSource, name="skill_source"), default=SkillSource.RESUME_EXTRACTION
    )

    candidate: Mapped["Candidate"] = relationship()
    skill: Mapped["Skill"] = relationship()
