"""
Covers spec section 51's required test cases: "Skill exact match, Skill
synonym, Missing required skill."
"""
from app.matching.skill_matcher import SkillMatchLevel, match_skills, skill_score


class TestSkillMatcher:
    def test_exact_match(self):
        summary = match_skills(
            required_and_preferred=[("Python", True, None)],
            candidate_skills=[("Python", 5.0)],
        )
        assert summary.results[0].level == SkillMatchLevel.EXACT
        assert summary.results[0].matched_candidate_skill == "Python"

    def test_skill_synonym_normalizes_to_canonical(self):
        """'pytorch' / 'torch' both canonicalize to 'PyTorch' (section 9)."""
        summary = match_skills(
            required_and_preferred=[("PyTorch", True, None)],
            candidate_skills=[("torch", 3.0)],
        )
        assert summary.results[0].level == SkillMatchLevel.EXACT

    def test_related_skill_is_not_claimed_as_exact(self):
        """Section 11's exact scenario: JD wants LangChain, candidate has
        LangGraph. Must be RELATED, never EXACT and never MISSING."""
        summary = match_skills(
            required_and_preferred=[("LangChain", True, None)],
            candidate_skills=[("LangGraph", 2.0)],
        )
        result = summary.results[0]
        assert result.level == SkillMatchLevel.RELATED
        assert result.matched_candidate_skill == "LangGraph"
        assert result.requirement_skill == "LangChain"  # never overwritten with the candidate's skill

    def test_missing_required_skill(self):
        summary = match_skills(
            required_and_preferred=[("Rust", True, None)],
            candidate_skills=[("Python", 5.0)],
        )
        assert summary.results[0].level == SkillMatchLevel.MISSING
        assert len(summary.missing_required) == 1

    def test_partial_match_insufficient_years(self):
        summary = match_skills(
            required_and_preferred=[("Python", True, 5.0)],
            candidate_skills=[("Python", 2.0)],
        )
        assert summary.results[0].level == SkillMatchLevel.PARTIAL

    def test_score_zero_when_all_missing(self):
        summary = match_skills(required_and_preferred=[("Rust", True, None)], candidate_skills=[])
        assert skill_score(summary) == 0.0

    def test_score_full_when_all_exact(self):
        summary = match_skills(
            required_and_preferred=[("Python", True, None), ("SQL", True, None)],
            candidate_skills=[("Python", 5.0), ("SQL", 3.0)],
        )
        assert skill_score(summary) == 100.0

    def test_preferred_skills_weighted_less_than_required(self):
        """Missing a required skill should hurt more than missing a
        preferred one."""
        missing_required = match_skills(
            required_and_preferred=[("Python", True, None), ("Docker", False, None)],
            candidate_skills=[("Docker", 1.0)],
        )
        missing_preferred = match_skills(
            required_and_preferred=[("Python", True, None), ("Docker", False, None)],
            candidate_skills=[("Python", 5.0)],
        )
        assert skill_score(missing_required) < skill_score(missing_preferred)

    def test_no_requirements_scores_perfect(self):
        summary = match_skills(required_and_preferred=[], candidate_skills=[("Python", 5.0)])
        assert skill_score(summary) == 100.0
