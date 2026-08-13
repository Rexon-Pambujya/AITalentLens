"""
Optional LLM layer for RELATED skill matches (section 11 / 61: the
LangChain-vs-LangGraph case). `skill_matcher.py` already decided this is a
RELATED, not EXACT, match using the deterministic skills graph - this module
never overrides that classification or the score it produces. It only adds
one recruiter-readable sentence judging whether the candidate's related
experience plausibly transfers, grounded in their own resume-derived
experience/project text.

Degrades to `None` (never raises) when the LLM is unavailable, exactly like
every other AI call in this codebase (section 62).
"""
from app.ai.base import LLMProvider
from app.ai.prompts import candidate_matching
from app.core.exceptions import LLMUnavailableError
from app.core.logging import get_logger

logger = get_logger(__name__)

MAX_CONTEXT_CHARS = 1500


async def evaluate_related_skill(
    llm: LLMProvider,
    *,
    required_skill: str,
    candidate_skill: str,
    resume_context: str,
) -> str | None:
    user_prompt = candidate_matching.build_user_prompt(
        required_skill=required_skill,
        candidate_skill=candidate_skill,
        resume_context=resume_context[:MAX_CONTEXT_CHARS],
    )
    try:
        text = await llm.generate(
            system_prompt=candidate_matching.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.2,
            max_tokens=100,
        )
        return text.strip()
    except LLMUnavailableError as exc:
        logger.warning("related_skill_evaluation_ai_unavailable", error=str(exc))
        return None
