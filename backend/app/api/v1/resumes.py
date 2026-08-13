from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_recruiter_or_admin
from app.core.exceptions import NotFoundError
from app.models.resume import Resume
from app.models.user import User
from app.schemas.resume import BatchUploadResult, ResumeRead, ResumeUploadResponse
from app.services.resume_service import intake_resume
from app.storage.factory import get_storage_backend
from app.workers.resume_tasks import process_resume_task

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/upload", response_model=BatchUploadResult, status_code=status.HTTP_202_ACCEPTED)
async def upload_resumes(
    files: list[UploadFile],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_recruiter_or_admin),
) -> BatchUploadResult:
    """Accepts one or many resumes (section 21: Batch Processing). Each
    file is validated/deduplicated/stored synchronously; the expensive
    parsing+AI+embedding work is handed off to Celery per file so this
    endpoint returns quickly regardless of batch size."""
    storage = get_storage_backend()
    results: list[ResumeUploadResponse] = []
    queued = duplicates = rejected = 0

    for upload in files:
        content = await upload.read()
        try:
            resume, is_duplicate = await intake_resume(
                db,
                storage,
                organization_id=current_user.organization_id,
                user_id=current_user.id,
                file_name=upload.filename or "resume",
                content=content,
                mime_type=upload.content_type or "application/octet-stream",
            )
        except Exception as exc:  # noqa: BLE001 - one bad file shouldn't fail the whole batch
            rejected += 1
            results.append(
                ResumeUploadResponse(
                    resume_id=UUID(int=0),
                    candidate_id=UUID(int=0),
                    file_name=upload.filename or "resume",
                    status="FAILED",
                    message=str(exc),
                )
            )
            continue

        if is_duplicate:
            duplicates += 1
            results.append(
                ResumeUploadResponse(
                    resume_id=resume.id,
                    candidate_id=resume.candidate_id,
                    file_name=upload.filename or "resume",
                    status=resume.parsed_status,
                    duplicate_of_resume_id=resume.id,
                    message="Possible duplicate candidate detected - matches a previously uploaded resume.",
                )
            )
            continue

        process_resume_task.delay(str(resume.id))
        queued += 1
        results.append(
            ResumeUploadResponse(
                resume_id=resume.id,
                candidate_id=resume.candidate_id,
                file_name=resume.file_name,
                status=resume.parsed_status,
                message="Queued for processing.",
            )
        )

    return BatchUploadResult(
        total=len(files), queued=queued, duplicates=duplicates, rejected=rejected, results=results
    )


@router.get("/{resume_id}", response_model=ResumeRead)
async def get_resume(
    resume_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeRead:
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalars().first()
    if resume is None:
        raise NotFoundError(f"Resume {resume_id} not found")
    return ResumeRead.model_validate(resume)


@router.get("/{resume_id}/status", response_model=ResumeRead)
async def get_resume_status(
    resume_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeRead:
    """Polled by the frontend upload UI (section 46) to drive the
    Processing... / Extracting... / Completed progress states."""
    return await get_resume(resume_id, db, current_user)
