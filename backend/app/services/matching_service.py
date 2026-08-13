"""
Orchestrates a full candidate-vs-job match: runs every matcher, combines
them via the scoring engine, builds the explanation, and persists a Match
row (section 34: persist so we don't re-run this on every page load).

Semantic scoring requires a query embedding for the job. If no LLM/
embedding backend is available, semantic_score degrades to a neutral 50
(not 0 - an unknown quantity shouldn't be scored as if disqualifying) and
this is recorded in `reasoning` so the recruiter knows semantic matching
didn't run, per section 62's graceful-degradation requirement.
"""
import uuid
from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.base import LLMProvider
from app.core.config import get_settings
from app.core.exceptions import LLMUnavailableError
from app.core.logging import get_logger
from app.matching.education_matcher import DegreeLevel, match_education, education_score
from app.matching.experience_matcher import ExperienceEntry, match_experience, experience_score
from app.matching.explanation_engine import build_explanation
from app.matching.llm_explanation import fallback_summary, generate_match_summary
from app.matching.llm_skill_evaluator import evaluate_related_skill
from app.matching.scoring_engine import (
    ComponentScores,
    RecommendationThresholds,
    ScoringWeights,
    calculate_overall_score,
    determine_recommendation,
)
from app.matching.semantic_matcher import semantic_match_candidate
from app.matching.skill_matcher import match_skills, skill_score
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.match import Match
from app.repositories.candidate_repository import list_candidate_skills

logger = get_logger(__name__)
settings = get_settings()

_DEGREE_LEVEL_MAP = {
    "none": DegreeLevel.NONE,
    "associate": DegreeLevel.ASSOCIATE,
    "bachelors": DegreeLevel.BACHELORS,
    "masters": DegreeLevel.MASTERS,
    "phd": DegreeLevel.DOCTORATE,
    "doctorate": DegreeLevel.DOCTORATE,
}


async def _get_semantic_score(
    db: AsyncSession, llm: LLMProvider, *, candidate_id: uuid.UUID, job_description: str
) -> tuple[float, bool]:
    """Returns (score, ran_successfully)."""
    try:
        query_embedding = (await llm.embed([job_description]))[0]
    except LLMUnavailableError:
        return 50.0, False

    result = await semantic_match_candidate(db, candidate_id=candidate_id, query_embedding=query_embedding)
    return result.score, True


async def calculate_match(
    db: AsyncSession, llm: LLMProvider, *, job_id: uuid.UUID, candidate_id: uuid.UUID, organization_id: uuid.UUID
) -> Match:
    job = (
        (
            await db.execute(
                select(Job)
                .options(selectinload(Job.requirements))
                .where(Job.id == job_id, Job.organization_id == organization_id)
            )
        )
        .scalars()
        .first()
    )
    candidate = (
        (
            await db.execute(
                select(Candidate)
                .options(
                    selectinload(Candidate.experiences),
                    selectinload(Candidate.educations),
                    selectinload(Candidate.projects),
                )
                .where(Candidate.id == candidate_id, Candidate.organization_id == organization_id)
            )
        )
        .scalars()
        .first()
    )
    if job is None or candidate is None:
        raise ValueError("Job or candidate not found in this organization")

    # --- Skills ---
    candidate_skill_rows = await list_candidate_skills(db, candidate_id=candidate_id)
    candidate_skills = [(cs.skill.name, cs.years_experience) for cs in candidate_skill_rows]
    required_and_preferred = [(r.skill, r.required, r.minimum_years) for r in job.requirements]
    skill_summary = match_skills(required_and_preferred=required_and_preferred, candidate_skills=candidate_skills)
    s_score = skill_score(skill_summary)

    # --- Semantic ---
    semantic_score, semantic_ran = await _get_semantic_score(
        db, llm, candidate_id=candidate_id, job_description=job.description
    )

    # --- Experience ---
    required_skill_names = [r.skill for r in job.requirements if r.required]
    experience_entries = [
        ExperienceEntry(
            years=e.years or 0.0,
            technologies=(e.description or "").split() if e.description else [],
            title=e.title,
            description=e.description,
        )
        for e in candidate.experiences
    ]
    exp_result = match_experience(
        entries=experience_entries, required_skills=required_skill_names, required_years=job.min_experience_years
    )
    e_score = experience_score(exp_result)

    # --- Education ---
    required_level = DegreeLevel.NONE
    required_field = None
    if job.education_requirements:
        # education_requirements is JSONB list of {"degree_level":..., "field":..., "required": bool}
        primary_req = next((r for r in job.education_requirements if r.get("required")), None) or (
            job.education_requirements[0] if job.education_requirements else None
        )
        if primary_req:
            required_level = _DEGREE_LEVEL_MAP.get(primary_req.get("degree_level", "none"), DegreeLevel.NONE)
            required_field = primary_req.get("field")

    candidate_degrees = [(ed.degree, ed.field) for ed in candidate.educations]
    edu_result = match_education(
        candidate_degrees=candidate_degrees, required_level=required_level, required_field=required_field
    )
    ed_score = education_score(edu_result)

    # --- Projects/certifications (kept simple for this phase: presence-based) ---
    project_score = 100.0 if candidate.projects else (50.0 if candidate_skills else 0.0)

    component_scores = ComponentScores(
        skills=s_score, semantic=semantic_score, experience=e_score, education=ed_score, projects=project_score
    )
    weights = ScoringWeights(
        skills=job.weight_skills,
        semantic=job.weight_semantic,
        experience=job.weight_experience,
        education=job.weight_education,
        projects=job.weight_projects,
    )
    overall = calculate_overall_score(component_scores, weights)
    recommendation = determine_recommendation(
        overall,
        RecommendationThresholds(
            strong_match=settings.RECOMMENDATION_STRONG_MATCH,
            good_match=settings.RECOMMENDATION_GOOD_MATCH,
            moderate_match=settings.RECOMMENDATION_MODERATE_MATCH,
        ),
    )

    explanation = build_explanation(
        skill_summary=skill_summary, experience_result=exp_result, education_result=edu_result,
        component_scores=component_scores,
    )
    if not semantic_ran:
        explanation.score_breakdown_narrative["semantic"] = (
            "50/100 (neutral default) - semantic matching did not run because the AI backend "
            "was unavailable; this score is not a reflection of the candidate's actual fit."
        )

    # For each RELATED skill (candidate has a different-but-similar skill,
    # e.g. LangGraph vs required LangChain), add one LLM-judged sentence on
    # whether it plausibly transfers - grounded in the candidate's own
    # experience/project text, never overriding the deterministic RELATED
    # classification or score. Best-effort: on AI-unavailable, the
    # deterministic note from build_explanation above is already present.
    if skill_summary.related:
        resume_context = "\n".join(
            f"{e.title or ''} at {e.company or ''}: {e.description or ''}" for e in candidate.experiences
        ) + "\n" + "\n".join(f"{p.name}: {p.description or ''}" for p in candidate.projects)
        for r in skill_summary.related:
            note = await evaluate_related_skill(
                llm,
                required_skill=r.requirement_skill,
                candidate_skill=r.matched_candidate_skill or "",
                resume_context=resume_context,
            )
            if note:
                explanation.improvements.append(f"{r.matched_candidate_skill} -> {r.requirement_skill}: {note}")

    candidate_label = candidate.name or "This candidate"
    recommendation_label = recommendation.value if hasattr(recommendation, "value") else recommendation
    llm_summary = await generate_match_summary(
        llm,
        candidate_name=candidate_label,
        job_title=job.title,
        overall_score=overall,
        recommendation=recommendation_label,
        strengths=explanation.strengths,
        improvements=explanation.improvements,
        missing_skills=[r.requirement_skill for r in skill_summary.missing_required],
    )
    llm_ran = llm_summary is not None
    summary = llm_summary or fallback_summary(
        candidate_name=candidate_label,
        overall_score=overall,
        recommendation=recommendation_label,
        strengths=explanation.strengths,
        missing_skills=[r.requirement_skill for r in skill_summary.missing_required],
    )

    # --- Persist (upsert on the unique (job_id, candidate_id) constraint) ---
    existing = (
        (await db.execute(select(Match).where(Match.job_id == job_id, Match.candidate_id == candidate_id)))
        .scalars()
        .first()
    )
    match = existing or Match(job_id=job_id, candidate_id=candidate_id)

    match.overall_score = overall
    match.skill_score = s_score
    match.semantic_score = semantic_score
    match.experience_score = e_score
    match.education_score = ed_score
    match.certification_score = 0.0
    match.project_score = project_score
    match.matched_skills = [
        {"skill": r.requirement_skill, "level": r.level.value, "candidate_years": r.candidate_years}
        for r in skill_summary.results
        if r.level in ("EXACT", "PARTIAL") or r.level.value in ("EXACT", "PARTIAL")
    ]
    match.missing_skills = [r.requirement_skill for r in skill_summary.missing_required]
    match.partial_skills = [r.requirement_skill for r in skill_summary.related]
    match.strengths = explanation.strengths
    match.improvements = explanation.improvements
    match.interview_focus = explanation.interview_focus
    match.evidence = [asdict(e) for e in explanation.evidence]
    match.recommendation = recommendation
    match.reasoning = explanation.score_breakdown_narrative
    match.summary = summary
    match.model_name = llm.model_name if llm_ran else "none (AI unavailable)"
    match.embedding_model = llm.embedding_model_name if semantic_ran else "none (AI unavailable)"
    match.prompt_version = settings.PROMPT_VERSION
    match.scoring_version = settings.SCORING_VERSION

    db.add(match)
    await db.commit()
    await db.refresh(match)
    return match
