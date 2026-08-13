"""
Hybrid scoring engine (section 10 - "one of the most important parts of
the project"). This is deliberately NOT an LLM call - it's a deterministic,
auditable, weighted formula over the outputs of the individual matchers.
Weights are configurable per job (Job.weight_* columns); recommendation
labels come from configurable thresholds, never from the LLM (section 16:
"Do not let the LLM decide these labels directly.").
"""
from dataclasses import dataclass

from app.models.enums import RecommendationLabel


@dataclass
class ScoringWeights:
    skills: float = 0.40
    semantic: float = 0.20
    experience: float = 0.20
    education: float = 0.10
    projects: float = 0.10

    def __post_init__(self):
        total = self.skills + self.semantic + self.experience + self.education + self.projects
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Scoring weights must sum to 1.0, got {total}")


@dataclass
class RecommendationThresholds:
    strong_match: int = 90
    good_match: int = 75
    moderate_match: int = 60


@dataclass
class ComponentScores:
    skills: float
    semantic: float
    experience: float
    education: float
    projects: float


def calculate_overall_score(scores: ComponentScores, weights: ScoringWeights) -> float:
    """The exact formula from spec section 10:

        overall_score = skill*0.40 + semantic*0.20 + experience*0.20
                       + education*0.10 + project_certification*0.10

    No hidden magic numbers - `weights` is the only tunable input, and it's
    persisted on the Job row so every score is reproducible.
    """
    overall = (
        scores.skills * weights.skills
        + scores.semantic * weights.semantic
        + scores.experience * weights.experience
        + scores.education * weights.education
        + scores.projects * weights.projects
    )
    return round(overall, 1)


def determine_recommendation(
    overall_score: float, thresholds: RecommendationThresholds
) -> RecommendationLabel:
    """Deterministic threshold lookup (section 16) - never delegated to the LLM."""
    if overall_score >= thresholds.strong_match:
        return RecommendationLabel.STRONG_MATCH
    if overall_score >= thresholds.good_match:
        return RecommendationLabel.GOOD_MATCH
    if overall_score >= thresholds.moderate_match:
        return RecommendationLabel.MODERATE_MATCH
    return RecommendationLabel.NOT_SUITABLE
