import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin


class Education(Base, UUIDPKMixin):
    __tablename__ = "educations"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    institution: Mapped[str | None] = mapped_column(String(255))
    degree: Mapped[str | None] = mapped_column(String(255))
    field: Mapped[str | None] = mapped_column(String(255))
    start_year: Mapped[int | None] = mapped_column(Integer)
    end_year: Mapped[int | None] = mapped_column(Integer)

    candidate: Mapped["Candidate"] = relationship(back_populates="educations")
