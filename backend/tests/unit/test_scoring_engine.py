"""Covers spec section 51's required 'Score calculation' and
'Recommendation thresholds' cases, and section 53's worked example."""
import pytest

from app.matching.scoring_engine import (
    ComponentScores,
    RecommendationThresholds,
    ScoringWeights,
    calculate_overall_score,
    determine_recommendation,
)
from app.models.enums import RecommendationLabel


class TestScoringEngine:
    def test_spec_section_53_worked_example(self):
        """Skill=90, Semantic=85, Experience=80, Education=100, Projects=70
        with 40/20/20/10/10 weighting -> 86.0"""
        scores = ComponentScores(skills=90, semantic=85, experience=80, education=100, projects=70)
        weights = ScoringWeights(skills=0.40, semantic=0.20, experience=0.20, education=0.10, projects=0.10)
        assert calculate_overall_score(scores, weights) == 86.0

    def test_weights_must_sum_to_one(self):
        with pytest.raises(ValueError):
            ScoringWeights(skills=0.5, semantic=0.5, experience=0.5, education=0.1, projects=0.1)

    def test_custom_weights_change_the_outcome(self):
        scores = ComponentScores(skills=90, semantic=85, experience=80, education=100, projects=70)
        default = calculate_overall_score(scores, ScoringWeights())
        skill_heavy = calculate_overall_score(
            scores, ScoringWeights(skills=0.6, semantic=0.1, experience=0.2, education=0.05, projects=0.05)
        )
        assert skill_heavy != default

    @pytest.mark.parametrize(
        "score,expected",
        [
            (95, RecommendationLabel.STRONG_MATCH),
            (90, RecommendationLabel.STRONG_MATCH),  # boundary is inclusive
            (89.9, RecommendationLabel.GOOD_MATCH),
            (75, RecommendationLabel.GOOD_MATCH),
            (74.9, RecommendationLabel.MODERATE_MATCH),
            (60, RecommendationLabel.MODERATE_MATCH),
            (59.9, RecommendationLabel.NOT_SUITABLE),
            (0, RecommendationLabel.NOT_SUITABLE),
        ],
    )
    def test_recommendation_thresholds(self, score, expected):
        thresholds = RecommendationThresholds(strong_match=90, good_match=75, moderate_match=60)
        assert determine_recommendation(score, thresholds) == expected

    def test_custom_thresholds_are_respected(self):
        """Section 16: thresholds must be configurable, not hardcoded."""
        lenient = RecommendationThresholds(strong_match=70, good_match=50, moderate_match=30)
        assert determine_recommendation(65, lenient) == RecommendationLabel.GOOD_MATCH
        strict = RecommendationThresholds(strong_match=95, good_match=85, moderate_match=70)
        assert determine_recommendation(65, strict) == RecommendationLabel.NOT_SUITABLE
