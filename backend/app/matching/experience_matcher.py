"""
Experience matching (section 13).

The spec is explicit that naive `total_years >= required_years` is wrong:
"JD requires 5 years ML experience. Candidate: 6 years software
engineering, 2 years ML. Do NOT simply calculate 6 >= 5. Relevant
experience should be approximately 2 years."

So this module classifies each experience entry's *relevance* to the JD's
required skill set (via keyword/skill overlap between the experience's
technologies/description and the job's required skills) and only counts
relevant years toward the requirement check. Total years is still tracked
and reported separately, since recruiters want to see both.
"""
from dataclasses import dataclass

from app.utils.normalization import normalize_text


@dataclass
class ExperienceEntry:
    years: float
    technologies: list[str]
    title: str | None = None
    description: str | None = None


@dataclass
class ExperienceMatchResult:
    total_years: float
    relevant_years: float
    required_years: float | None
    relevance_percentage: float  # relevant_years / total_years, 0-100
    experience_match_percentage: float  # relevant_years / required_years, 0-100 (capped)


def _is_relevant(entry: ExperienceEntry, required_skill_terms: set[str]) -> bool:
    """An experience entry counts as relevant if any of its listed
    technologies, or any required-skill term appearing in its free-text
    title/description, overlaps the job's required skills."""
    entry_terms = {normalize_text(t) for t in entry.technologies}
    if entry_terms & required_skill_terms:
        return True

    haystack = normalize_text(f"{entry.title or ''} {entry.description or ''}")
    return any(term in haystack for term in required_skill_terms if term)


def match_experience(
    *,
    entries: list[ExperienceEntry],
    required_skills: list[str],
    required_years: float | None,
) -> ExperienceMatchResult:
    """Pure function - fully unit-testable, no DB/network access."""
    required_terms = {normalize_text(s) for s in required_skills}

    total_years = round(sum(e.years for e in entries), 1)
    relevant_years = round(sum(e.years for e in entries if _is_relevant(e, required_terms)), 1)

    relevance_pct = round((relevant_years / total_years) * 100, 1) if total_years > 0 else 0.0

    if required_years and required_years > 0:
        match_pct = round(min(relevant_years / required_years, 1.0) * 100, 1)
    else:
        # No explicit requirement - nothing to fail against.
        match_pct = 100.0

    return ExperienceMatchResult(
        total_years=total_years,
        relevant_years=relevant_years,
        required_years=required_years,
        relevance_percentage=relevance_pct,
        experience_match_percentage=match_pct,
    )


def experience_score(result: ExperienceMatchResult) -> float:
    return result.experience_match_percentage
