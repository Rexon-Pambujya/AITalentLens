from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import ResumeParsedStatus


class ResumeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    candidate_id: UUID
    file_name: str
    mime_type: str
    parsed_status: ResumeParsedStatus
    processing_error: str | None
    created_at: datetime


class ResumeUploadResponse(BaseModel):
    """Returned immediately on upload - the actual processing happens
    async in Celery (section 7)."""

    resume_id: UUID
    candidate_id: UUID
    file_name: str
    status: ResumeParsedStatus
    duplicate_of_resume_id: UUID | None = None
    message: str


class BatchUploadResult(BaseModel):
    total: int
    queued: int
    duplicates: int
    rejected: int
    results: list[ResumeUploadResponse]
