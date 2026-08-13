import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import get_settings
from app.db.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import ResumeParsedStatus

settings = get_settings()


class Resume(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "resumes"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # SHA-256
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(150), nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text)
    parsed_status: Mapped[ResumeParsedStatus] = mapped_column(
        SAEnum(ResumeParsedStatus, name="resume_parsed_status"),
        nullable=False,
        default=ResumeParsedStatus.QUEUED,
    )
    processing_error: Mapped[str | None] = mapped_column(Text)

    candidate: Mapped["Candidate"] = relationship(back_populates="resumes")
    embeddings: Mapped[list["ResumeEmbedding"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan"
    )


class ResumeEmbedding(Base, UUIDPKMixin):
    """Chunk-level embeddings (NOT one whole-resume embedding - see spec
    section 12) so semantic search can match on the specific paragraph that
    actually demonstrates a skill."""

    __tablename__ = "resume_embeddings"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.EMBEDDING_DIMENSIONS), nullable=False)

    resume: Mapped["Resume"] = relationship(back_populates="embeddings")
