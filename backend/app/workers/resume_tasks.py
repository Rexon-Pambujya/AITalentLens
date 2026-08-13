"""
The async resume processing pipeline (section 7), run as a Celery task.

Celery tasks are synchronous by nature; SQLAlchemy's async engine needs an
event loop, so each task creates one short-lived loop via `asyncio.run`
around a dedicated DB session - no session/connection is shared across
tasks or requests.
"""
import asyncio
import uuid

from sqlalchemy import select

from app.ai.factory import build_llm_provider
from app.core.logging import get_logger
from app.db.worker_session import worker_db_session
from app.embeddings.embedding_service import embed_chunks
from app.extraction.resume_extractor import extract_candidate_profile
from app.ingestion.docx_parser import extract_text_from_docx
from app.ingestion.pdf_parser import extract_text_from_pdf
from app.ingestion.text_cleaner import chunk_text_for_embedding, clean_text
from app.models.candidate import Candidate
from app.models.enums import ResumeParsedStatus
from app.models.resume import Resume, ResumeEmbedding
from app.services.audit_service import record_audit_log
from app.services.candidate_service import apply_extracted_profile
from app.storage.factory import get_storage_backend
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


async def _process_resume_async(resume_id: str) -> None:
    async with worker_db_session() as db:
        resume = (await db.execute(select(Resume).where(Resume.id == uuid.UUID(resume_id)))).scalars().first()
        if resume is None:
            logger.error("resume_not_found", resume_id=resume_id)
            return

        resume.parsed_status = ResumeParsedStatus.PROCESSING
        await db.commit()

        # A fresh, uncached provider bound to THIS task's event loop - never
        # the cached get_llm_provider() singleton, which would carry an
        # httpx.AsyncClient from a previous task's now-closed event loop and
        # fail every call after the first with "Event loop is closed" (same
        # class of issue worker_db_session.py documents for the DB engine).
        llm = build_llm_provider()
        try:
            storage = get_storage_backend()
            content = await storage.read(resume.storage_path)

            # --- Text extraction ---
            if resume.mime_type == "application/pdf":
                raw_text = extract_text_from_pdf(content)
            else:
                raw_text = extract_text_from_docx(content)

            cleaned = clean_text(raw_text)
            resume.raw_text = cleaned
            resume.parsed_status = ResumeParsedStatus.EXTRACTED
            await db.commit()

            # --- LLM structured extraction (graceful degradation: if the
            # AI backend is unavailable, we still keep raw_text and move on
            # rather than failing the whole resume - section 62) ---
            profile = await extract_candidate_profile(llm, resume_text=cleaned)

            candidate = (
                (await db.execute(select(Candidate).where(Candidate.id == resume.candidate_id)))
                .scalars()
                .first()
            )
            if profile is not None:
                await apply_extracted_profile(db, candidate=candidate, profile=profile)
                await db.commit()
            else:
                logger.info("resume_ai_extraction_skipped", resume_id=resume_id, reason="AI unavailable or invalid output")

            # --- Embeddings (also degrades gracefully) ---
            chunks = chunk_text_for_embedding(cleaned)
            vectors = await embed_chunks(llm, chunks)
            if vectors:
                for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
                    db.add(
                        ResumeEmbedding(resume_id=resume.id, chunk_text=chunk, chunk_index=idx, embedding=vector)
                    )
                resume.parsed_status = ResumeParsedStatus.COMPLETED
            else:
                # Extraction/text succeeded but no embeddings - still a
                # usable resume for keyword search and deterministic skill
                # matching, just not semantic search yet.
                resume.parsed_status = ResumeParsedStatus.COMPLETED
                logger.info("resume_completed_without_embeddings", resume_id=resume_id)

            await record_audit_log(
                db, user_id=None, action="RESUME_PROCESSED", resource_type="resume", resource_id=resume.id,
                metadata={"had_ai_extraction": profile is not None, "had_embeddings": bool(vectors)},
            )
            await db.commit()

        except Exception as exc:  # noqa: BLE001 - this boundary must never re-raise into Celery's retry storm silently
            logger.error("resume_processing_failed", resume_id=resume_id, error=str(exc))
            resume.parsed_status = ResumeParsedStatus.FAILED
            resume.processing_error = str(exc)[:2000]
            await db.commit()
        finally:
            await llm.aclose()


@celery_app.task(name="resumes.process_resume", bind=True, max_retries=2)
def process_resume_task(self, resume_id: str) -> None:
    asyncio.run(_process_resume_async(resume_id))
