from app.ai.base import LLMProvider, StructuredGenerationError
from app.ai.prompts import jd_extraction
from app.core.exceptions import LLMUnavailableError
from app.core.logging import get_logger
from app.extraction.schemas import JobProfile

logger = get_logger(__name__)

MAX_JD_CHARS_FOR_EXTRACTION = 8000


async def extract_job_profile(llm: LLMProvider, *, jd_text: str) -> JobProfile | None:
    truncated = jd_text[:MAX_JD_CHARS_FOR_EXTRACTION]
    user_prompt = jd_extraction.build_user_prompt(truncated)

    try:
        profile = await llm.generate_structured(
            system_prompt=jd_extraction.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_schema=JobProfile,
            temperature=0.0,
        )
        logger.info("jd_extraction_succeeded", provider=llm.provider_name, model=llm.model_name)
        return profile
    except LLMUnavailableError as exc:
        logger.warning("jd_extraction_ai_unavailable", error=str(exc))
        return None
    except StructuredGenerationError as exc:
        logger.warning("jd_extraction_invalid_output", error=str(exc))
        return None
