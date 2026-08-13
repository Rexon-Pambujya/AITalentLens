import uuid
from datetime import date

from pgvector.sqlalchemy import Vector
from sqlalchemy import Date, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import get_settings
from app.db.base import Base, UUIDPKMixin

settings = get_settings()


class Experience(Base, UUIDPKMixin):
    """A single work-history entry. `years` is computed from
    start_date/end_date at extraction time and is what the experience
    matcher sums/classifies against JD requirements (section 13)."""

    __tablename__ = "experiences"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(255))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)  # null == "current"
    description: Mapped[str | None] = mapped_column(Text)
    years: Mapped[float | None] = mapped_column(Float)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(settings.EMBEDDING_DIMENSIONS))

    candidate: Mapped["Candidate"] = relationship(back_populates="experiences")
