"""Covers spec section 51's required 'Education equivalency' case."""
from app.matching.education_matcher import DegreeLevel, match_education, parse_degree_level


class TestEducationMatcher:
    def test_equivalent_degree_names_parse_to_same_level(self):
        """'B.Tech Computer Science' / 'B.E. Information Technology' /
        'M.Sc Computer Science' - section 14's exact example."""
        assert parse_degree_level("B.Tech Computer Science") == DegreeLevel.BACHELORS
        assert parse_degree_level("B.E. Information Technology") == DegreeLevel.BACHELORS
        assert parse_degree_level("M.Sc Computer Science") == DegreeLevel.MASTERS

    def test_related_field_not_rejected(self):
        """IT and CS should be treated as related fields, not auto-rejected."""
        result = match_education(
            candidate_degrees=[("B.E. Information Technology", "Information Technology")],
            required_level=DegreeLevel.BACHELORS,
            required_field="Computer Science",
        )
        assert result.meets_level_requirement is True
        assert result.field_match is True
        assert result.score == 100.0

    def test_overqualified_candidate_meets_requirement(self):
        result = match_education(
            candidate_degrees=[("M.Sc Computer Science", "Computer Science")],
            required_level=DegreeLevel.BACHELORS,
            required_field="Computer Science",
        )
        assert result.meets_level_requirement is True

    def test_underqualified_gets_partial_credit_not_zero(self):
        result = match_education(
            candidate_degrees=[("B.Tech Computer Science", "Computer Science")],
            required_level=DegreeLevel.MASTERS,
            required_field=None,
        )
        assert result.meets_level_requirement is False
        assert 0 < result.score < 100

    def test_no_degree_at_all_scores_zero_against_a_requirement(self):
        result = match_education(candidate_degrees=[], required_level=DegreeLevel.BACHELORS, required_field=None)
        assert result.score == 0.0

    def test_no_degree_and_no_requirement_scores_perfect(self):
        result = match_education(candidate_degrees=[], required_level=DegreeLevel.NONE, required_field=None)
        assert result.score == 100.0

    def test_unrelated_field_correct_level_partial_credit(self):
        result = match_education(
            candidate_degrees=[("Bachelor of Arts", "Fine Arts")],
            required_level=DegreeLevel.BACHELORS,
            required_field="Computer Science",
        )
        assert result.meets_level_requirement is True
        assert result.field_match is False
        assert result.score < 100.0
