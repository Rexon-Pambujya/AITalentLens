"""
Explanation engine (section 15: Explainable AI).

Deliberately assembled DETERMINISTICALLY from the matchers' own outputs,
not generated freely by an LLM - every strength/gap/evidence string is
built directly from a SkillMatchResult, ExperienceMatchResult, etc. This
is what "Do NOT hallucinate evidence" (section 15) means in practice: the
evidence shown IS the evidence used, not a paraphrase an LLM invented.

An optional LLM prose polish pass can be layered on top later (turning
these structured facts into flowing recruiter-friendly sentences), but
even then the LLM would only be reformatting these exact facts, with the
facts themselves as a hard constraint - never asked to invent new ones.
"""
from dataclasses import dataclass, field

from app.matching.education_matcher import EducationMatchResult
from app.matching.experience_matcher import ExperienceMatchResult
from app.matching.scoring_engine import ComponentScores
from app.matching.skill_matcher import SkillMatchLevel, SkillMatchSummary


@dataclass
class Evidence:
    claim: str
    source: str
    text: str | None = None


@dataclass
class Explanation:
    strengths: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
    interview_focus: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    score_breakdown_narrative: dict[str, str] = field(default_factory=dict)


def build_explanation(
    *,
    skill_summary: SkillMatchSummary,
    experience_result: ExperienceMatchResult,
    education_result: EducationMatchResult,
    component_scores: ComponentScores,
) -> Explanation:
    strengths: list[str] = []
    improvements: list[str] = []
    interview_focus: list[str] = []
    evidence: list[Evidence] = []

    # --- Skills ---
    for r in skill_summary.matched_required:
        years_note = f" ({r.candidate_years} yrs)" if r.candidate_years else ""
        strengths.append(f"{r.requirement_skill}{years_note} - matches required skill")
        if r.evidence:
            evidence.append(Evidence(claim=f"Has {r.requirement_skill} experience", source="Skills", text=r.evidence))

    for r in skill_summary.related:
        note = f"Has {r.matched_candidate_skill}, a related skill to required '{r.requirement_skill}' - not identical, worth confirming depth in interview"
        improvements.append(note)
        interview_focus.append(f"Confirm whether {r.matched_candidate_skill} experience transfers to {r.requirement_skill}")

    for r in skill_summary.missing_required:
        improvements.append(f"No evidence of required skill: {r.requirement_skill}")
        interview_focus.append(f"Assess {r.requirement_skill} proficiency directly")

    if skill_summary.matched_preferred:
        names = ", ".join(r.requirement_skill for r in skill_summary.matched_preferred)
        strengths.append(f"Also has preferred skills: {names}")

    # --- Experience ---
    if experience_result.required_years:
        if experience_result.experience_match_percentage >= 100:
            strengths.append(
                f"{experience_result.relevant_years} years of directly relevant experience meets the "
                f"{experience_result.required_years}-year requirement"
            )
        elif experience_result.relevant_years > 0:
            improvements.append(
                f"Only {experience_result.relevant_years} of {experience_result.required_years} required "
                f"years are directly relevant (total experience: {experience_result.total_years} years)"
            )
            interview_focus.append("Probe depth of directly relevant hands-on experience vs. adjacent work")
        else:
            improvements.append(
                f"No directly relevant experience found against the {experience_result.required_years}-year requirement"
            )

    # --- Education ---
    if education_result.required_level.value > 0:
        if education_result.meets_level_requirement and education_result.field_match is not False:
            strengths.append("Education meets the role's degree and field requirements")
        elif not education_result.meets_level_requirement:
            improvements.append("Highest education level found is below the role's stated requirement")
        elif education_result.field_match is False:
            improvements.append("Degree level meets the requirement, but field of study differs")

    return Explanation(
        strengths=strengths,
        improvements=improvements,
        interview_focus=interview_focus,
        evidence=evidence,
        score_breakdown_narrative={
            "skills": f"{component_scores.skills}/100 - based on {len(skill_summary.results)} requirements checked",
            "semantic": f"{component_scores.semantic}/100 - based on resume content similarity to the job description",
            "experience": f"{component_scores.experience}/100 - {experience_result.relevant_years} of "
            f"{experience_result.required_years or 'unspecified'} required relevant years",
            "education": f"{component_scores.education}/100",
            "projects": f"{component_scores.projects}/100",
        },
    )
