"""
Optional LLM prose layer on top of the deterministic explanation (section 26:
AI Insights / "Why this candidate?"). This NEVER computes scores or decides
strengths/gaps itself - `explanation_engine.py` already did that from the
matchers' raw output. This module only asks the LLM to turn those
already-decided facts into a short recruiter-readable paragraph, with the
facts themselves passed as a hard constraint (see prompts/explanation.py).

Degrades to `None` (never raises) when the LLM is unavailable, exactly like
every other AI call in this codebase (section 62) - callers fall back to a
deterministic sentence built from the same facts.
"""
from app.ai.base import LLMProvider
from app.ai.prompts import explanation
from app.core.exceptions import LLMUnavailableError
from app.core.logging import get_logger

logger = get_logger(__name__)

MAX_STRENGTHS_FOR_PROMPT = 6
MAX_IMPROVEMENTS_FOR_PROMPT = 6


async def generate_match_summary(
    llm: LLMProvider,
    *,
    candidate_name: str,
    job_title: str,
    overall_score: float,
    recommendation: str,
    strengths: list[str],
    improvements: list[str],
    missing_skills: list[str],
) -> str | None:
    user_prompt = explanation.build_user_prompt(
        candidate_name=candidate_name,
        job_title=job_title,
        overall_score=overall_score,
        recommendation=recommendation,
        strengths=strengths[:MAX_STRENGTHS_FOR_PROMPT],
        improvements=improvements[:MAX_IMPROVEMENTS_FOR_PROMPT],
        missing_skills=missing_skills,
    )
    try:
        text = await llm.generate(
            system_prompt=explanation.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.2,
            max_tokens=220,
        )
        return text.strip()
    except LLMUnavailableError as exc:
        logger.warning("match_summary_ai_unavailable", error=str(exc))
        return None


def fallback_summary(*, candidate_name: str, overall_score: float, recommendation: str, strengths: list[str], missing_skills: list[str]) -> str:
    """Deterministic sentence used when the LLM is unavailable, so the UI
    never has a blank "why" section (section 62: graceful degradation)."""
    label = recommendation.replace("_", " ").title()
    parts = [f"{candidate_name} scored {round(overall_score)}/100 ({label})."]
    if strengths:
        parts.append(f"Key strengths: {'; '.join(strengths[:2])}.")
    if missing_skills:
        parts.append(f"Missing: {', '.join(missing_skills[:3])}.")
    return " ".join(parts)
