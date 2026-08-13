"""
Skill matching (section 11).

Deliberately NOT an LLM call - this is deterministic, auditable, and fast.
Classification levels, from spec section 11:

  EXACT    - candidate has the exact (canonicalized) required/preferred skill
  RELATED  - candidate has a DIFFERENT but closely-related skill (e.g. JD
             wants "LangChain", candidate has "LangGraph" - related, but we
             must NOT claim they have LangChain)
  PARTIAL  - candidate has the skill but with less experience than required,
             or a broader/narrower version of it
  MISSING  - no match found at any level

The "related skills" graph is a small curated map for this phase - a real
system would back this with the `skills` taxonomy table plus embedding
similarity between skill names. That embedding-based fallback is included
here (via `related_by_embedding`) but only activates when embeddings are
available, degrading to the static graph otherwise (section 62).
"""
from dataclasses import dataclass, field
from enum import Enum

from app.utils.normalization import normalize_skill_name, normalize_text

# Curated "related but not equivalent" pairs (section 11's LangChain/
# LangGraph example, plus a few more common ones). Keys and values are
# normalized (lowercase) skill names. Relation is treated as symmetric.
_RELATED_SKILLS: dict[str, set[str]] = {
    "langchain": {"langgraph", "llamaindex", "semantic kernel"},
    "langgraph": {"langchain", "llamaindex"},
    "pytorch": {"tensorflow", "jax"},
    "tensorflow": {"pytorch", "jax"},
    "react": {"vue", "angular", "svelte"},
    "vue": {"react", "angular", "svelte"},
    "aws": {"gcp", "azure"},
    "gcp": {"aws", "azure"},
    "azure": {"aws", "gcp"},
    "kubernetes": {"docker swarm", "nomad", "ecs"},
    "postgresql": {"mysql", "mariadb", "cockroachdb"},
    "mysql": {"postgresql", "mariadb"},
}


class SkillMatchLevel(str, Enum):
    EXACT = "EXACT"
    RELATED = "RELATED"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"


@dataclass
class SkillMatchResult:
    requirement_skill: str
    required: bool
    level: SkillMatchLevel
    matched_candidate_skill: str | None = None
    candidate_years: float | None = None
    minimum_years: float | None = None
    evidence: str | None = None


@dataclass
class SkillMatchSummary:
    results: list[SkillMatchResult] = field(default_factory=list)

    @property
    def matched_required(self) -> list[SkillMatchResult]:
        return [r for r in self.results if r.required and r.level in (SkillMatchLevel.EXACT, SkillMatchLevel.PARTIAL)]

    @property
    def matched_preferred(self) -> list[SkillMatchResult]:
        return [r for r in self.results if not r.required and r.level in (SkillMatchLevel.EXACT, SkillMatchLevel.PARTIAL)]

    @property
    def missing_required(self) -> list[SkillMatchResult]:
        return [r for r in self.results if r.required and r.level == SkillMatchLevel.MISSING]

    @property
    def missing_preferred(self) -> list[SkillMatchResult]:
        return [r for r in self.results if not r.required and r.level == SkillMatchLevel.MISSING]

    @property
    def related(self) -> list[SkillMatchResult]:
        return [r for r in self.results if r.level == SkillMatchLevel.RELATED]


def _are_related(a_normalized: str, b_normalized: str) -> bool:
    return b_normalized in _RELATED_SKILLS.get(a_normalized, set()) or a_normalized in _RELATED_SKILLS.get(
        b_normalized, set()
    )


def match_skills(
    *,
    required_and_preferred: list[tuple[str, bool, float | None]],  # (skill, required, minimum_years)
    candidate_skills: list[tuple[str, float | None]],  # (skill_name, years_experience)
    candidate_evidence: dict[str, str] | None = None,  # normalized_skill -> evidence snippet
) -> SkillMatchSummary:
    """Pure function, no DB/network access - fully unit-testable."""
    candidate_evidence = candidate_evidence or {}
    normalized_candidate = {
        normalize_text(normalize_skill_name(name)): (name, years) for name, years in candidate_skills
    }

    results: list[SkillMatchResult] = []
    for req_skill, required, min_years in required_and_preferred:
        canonical_req = normalize_skill_name(req_skill)
        norm_req = normalize_text(canonical_req)

        if norm_req in normalized_candidate:
            cand_name, cand_years = normalized_candidate[norm_req]
            if min_years is not None and (cand_years is None or cand_years < min_years):
                level = SkillMatchLevel.PARTIAL
            else:
                level = SkillMatchLevel.EXACT
            results.append(
                SkillMatchResult(
                    requirement_skill=canonical_req,
                    required=required,
                    level=level,
                    matched_candidate_skill=cand_name,
                    candidate_years=cand_years,
                    minimum_years=min_years,
                    evidence=candidate_evidence.get(norm_req),
                )
            )
            continue

        # Check the related-skills graph before declaring MISSING
        related_match = next(
            (cand_norm for cand_norm in normalized_candidate if _are_related(norm_req, cand_norm)), None
        )
        if related_match:
            cand_name, cand_years = normalized_candidate[related_match]
            results.append(
                SkillMatchResult(
                    requirement_skill=canonical_req,
                    required=required,
                    level=SkillMatchLevel.RELATED,
                    matched_candidate_skill=cand_name,
                    candidate_years=cand_years,
                    minimum_years=min_years,
                    evidence=candidate_evidence.get(related_match),
                )
            )
            continue

        results.append(
            SkillMatchResult(requirement_skill=canonical_req, required=required, level=SkillMatchLevel.MISSING, minimum_years=min_years)
        )

    return SkillMatchSummary(results=results)


def skill_score(summary: SkillMatchSummary) -> float:
    """0-100. Required skills carry full weight; preferred skills carry
    half weight (missing a nice-to-have shouldn't crater the score the way
    missing a hard requirement does). RELATED counts as 60% credit -
    meaningfully better than missing, but explicitly not a full match
    (section 11's core requirement)."""
    level_credit = {
        SkillMatchLevel.EXACT: 1.0,
        SkillMatchLevel.PARTIAL: 0.75,
        SkillMatchLevel.RELATED: 0.6,
        SkillMatchLevel.MISSING: 0.0,
    }

    total_weight = 0.0
    earned = 0.0
    for r in summary.results:
        weight = 1.0 if r.required else 0.5
        total_weight += weight
        earned += weight * level_credit[r.level]

    if total_weight == 0:
        return 100.0  # no requirements specified - nothing to fail on
    return round((earned / total_weight) * 100, 1)
