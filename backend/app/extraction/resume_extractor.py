"""
Resume information extraction.

`extract_candidate_profile` is the only entry point the rest of the app
should call. It NEVER lets a raw LLM/network exception escape - on any AI
failure it returns `None` and the caller (resume_service / Celery task)
falls back to whatever deterministic extraction is possible (regex-based
contact info, raw text storage) per section 62.
"""
from app.ai.base import LLMProvider, StructuredGenerationError
from app.ai.prompts import resume_extraction
from app.core.exceptions import LLMUnavailableError
from app.core.logging import get_logger
from app.extraction.schemas import CandidateProfile

logger = get_logger(__name__)

MAX_RESUME_CHARS_FOR_EXTRACTION = 12000  # keep prompt cost/latency bounded


async def extract_candidate_profile(
    llm: LLMProvider, *, resume_text: str
) -> CandidateProfile | None:
    truncated = resume_text[:MAX_RESUME_CHARS_FOR_EXTRACTION]
    user_prompt = resume_extraction.build_user_prompt(truncated)

    try:
        profile = await llm.generate_structured(
            system_prompt=resume_extraction.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_schema=CandidateProfile,
            temperature=0.0,
        )
        logger.info("resume_extraction_succeeded", provider=llm.provider_name, model=llm.model_name)
        return profile
    except LLMUnavailableError as exc:
        logger.warning("resume_extraction_ai_unavailable", error=str(exc))
        return None
    except StructuredGenerationError as exc:
        logger.warning("resume_extraction_invalid_output", error=str(exc))
        return None
