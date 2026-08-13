"""Covers spec section 51's required 'Experience mismatch' case."""
from app.matching.experience_matcher import ExperienceEntry, experience_score, match_experience


class TestExperienceMatcher:
    def test_spec_section_13_exact_scenario(self):
        """'JD requires 5 years ML experience. Candidate: 6 years software
        engineering, 2 years ML. Do NOT simply calculate 6 >= 5. Relevant
        experience should be approximately 2 years.'"""
        entries = [
            ExperienceEntry(years=4.0, technologies=["Java", "Spring"], title="Software Engineer",
                             description="Built backend services using Java and Spring."),
            ExperienceEntry(years=2.0, technologies=["Python", "PyTorch"], title="ML Engineer",
                             description="Trained ML models for fraud detection."),
        ]
        result = match_experience(entries=entries, required_skills=["Machine Learning", "Python", "PyTorch"], required_years=5.0)

        assert result.total_years == 6.0
        assert result.relevant_years == 2.0
        assert result.experience_match_percentage == 40.0  # 2/5, NOT the naive 6>=5 -> 100%

    def test_fully_relevant_experience_meets_requirement(self):
        entries = [ExperienceEntry(years=6.0, technologies=["Python", "PyTorch"], title="ML Engineer")]
        result = match_experience(entries=entries, required_skills=["Python", "PyTorch"], required_years=5.0)
        assert result.experience_match_percentage == 100.0  # capped, not >100

    def test_no_required_years_specified_does_not_penalize(self):
        entries = [ExperienceEntry(years=1.0, technologies=["Java"])]
        result = match_experience(entries=entries, required_skills=["Python"], required_years=None)
        assert result.experience_match_percentage == 100.0

    def test_zero_relevant_experience(self):
        entries = [ExperienceEntry(years=5.0, technologies=["Marketing"], title="Marketing Manager")]
        result = match_experience(entries=entries, required_skills=["Python", "PyTorch"], required_years=3.0)
        assert result.relevant_years == 0.0
        assert result.experience_match_percentage == 0.0
        assert result.total_years == 5.0

    def test_relevance_detected_via_description_keywords(self):
        entries = [ExperienceEntry(years=3.0, technologies=[], title="Engineer",
                                    description="Extensive Kubernetes deployment experience.")]
        result = match_experience(entries=entries, required_skills=["Kubernetes"], required_years=2.0)
        assert result.relevant_years == 3.0
