import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UpdatedAtMixin
from app.models.enums import PipelineStatus


class CandidatePipeline(Base, UpdatedAtMixin):
    """Tracks where a candidate sits in the hiring funnel *for a specific
    job* - a candidate can be SHORTLISTED for one job and REJECTED for
    another simultaneously."""

    __tablename__ = "candidate_pipeline"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), primary_key=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True
    )
    status: Mapped[PipelineStatus] = mapped_column(
        SAEnum(PipelineStatus, name="pipeline_status"), nullable=False, default=PipelineStatus.NEW
    )

    candidate: Mapped["Candidate"] = relationship()
    job: Mapped["Job"] = relationship()
