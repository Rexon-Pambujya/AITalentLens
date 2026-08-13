"""
Resume intake: everything that happens synchronously during the upload
request, BEFORE the async Celery pipeline takes over (section 7 pipeline:
Upload -> Validation -> Deduplication -> Document Storage, then async from
Text Extraction onward).
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.core.config import get_settings
from app.core.exceptions import UnsupportedDocumentError, ValidationError
from app.models.candidate import Candidate
from app.models.enums import ResumeParsedStatus
from app.models.resume import Resume
from app.repositories.resume_repository import find_resume_by_hash
from app.services.audit_service import record_audit_log
from app.storage.base import StorageBackend
from app.utils.hashing import sha256_bytes

settings = get_settings()


def validate_upload(*, file_name: str, content: bytes, mime_type: str) -> None:
    if mime_type not in settings.ALLOWED_RESUME_MIME_TYPES:
        raise UnsupportedDocumentError(
            f"Unsupported file type '{mime_type}'. Allowed: PDF, DOCX."
        )
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise ValidationError(f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB upload limit")
    if len(content) == 0:
        raise ValidationError("Uploaded file is empty")


async def intake_resume(
    db: AsyncSession,
    storage: StorageBackend,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    file_name: str,
    content: bytes,
    mime_type: str,
) -> tuple[Resume, bool]:
    """Returns (resume, is_duplicate). On duplicate, returns the EXISTING
    resume rather than creating a new candidate/resume row (section 20)."""
    validate_upload(file_name=file_name, content=content, mime_type=mime_type)
    file_hash = sha256_bytes(content)

    existing = await find_resume_by_hash(db, organization_id=organization_id, file_hash=file_hash)
    if existing is not None:
        # A prior upload of this exact file may have finished (COMPLETED or
        # FAILED) without ever actually extracting anything - e.g. the AI
        # backend was unreachable at the time. Treating that as a
        # permanent duplicate would leave the candidate blank forever with
        # no way to fix it short of a different file. Only skip
        # reprocessing for a TRUE duplicate: one that already produced a
        # named candidate.
        existing_candidate = (
            await db.execute(select(Candidate).where(Candidate.id == existing.candidate_id))
        ).scalars().first()
        already_extracted = bool(existing_candidate and existing_candidate.name)

        if already_extracted:
            await record_audit_log(
                db, user_id=user_id, action="RESUME_DUPLICATE_DETECTED", resource_type="resume",
                resource_id=existing.id, metadata={"file_name": file_name},
            )
            await db.commit()
            return existing, True

        existing.parsed_status = ResumeParsedStatus.QUEUED
        existing.processing_error = None
        await record_audit_log(
            db, user_id=user_id, action="RESUME_REPROCESS_QUEUED", resource_type="resume",
            resource_id=existing.id,
            metadata={"file_name": file_name, "reason": "prior attempt produced no extracted data"},
        )
        await db.commit()
        await db.refresh(existing)
        return existing, False

    # Candidate identity isn't known yet (extraction hasn't run) - create a
    # placeholder now so the FK is satisfiable; candidate_service fills in
    # name/email/etc once extraction completes.
    candidate = Candidate(organization_id=organization_id)
    db.add(candidate)
    await db.flush()

    storage_key = storage.build_key(
        organization_id=str(organization_id), candidate_id=str(candidate.id), file_name=file_name
    )
    storage_path = await storage.save(key=storage_key, content=content, content_type=mime_type)

    resume = Resume(
        candidate_id=candidate.id,
        file_name=file_name,
        file_hash=file_hash,
        storage_path=storage_path,
        mime_type=mime_type,
        parsed_status=ResumeParsedStatus.QUEUED,
    )
    db.add(resume)
    await db.flush()

    await record_audit_log(
        db, user_id=user_id, action="RESUME_UPLOADED", resource_type="resume", resource_id=resume.id,
        metadata={"file_name": file_name, "candidate_id": str(candidate.id)},
    )
    await db.commit()
    await db.refresh(resume)
    return resume, False
