"""
Applies a validated `CandidateProfile` (LLM extraction output) onto the
Candidate row and its related tables (Experience, Education, Certification,
Project, CandidateSkill). Called by the Celery pipeline after extraction
succeeds - never called with unvalidated data (see extraction/schemas.py).
"""
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.extraction.schemas import CandidateProfile
from app.models.candidate import Candidate
from app.models.certification import Certification
from app.models.education import Education
from app.models.experience import Experience
from app.models.project import Project
from app.models.recruiter_note import RecruiterNote
from app.models.skill import CandidateSkill, Skill
from app.utils.normalization import normalize_skill_name, normalize_text


def _parse_year(value: str | None) -> date | None:
    """Best-effort parse of LLM-provided date-ish strings ('2021-03', '2021')
    into a `date`. Never raises - unparseable input just becomes None,
    consistent with 'don't invent data' (section 8)."""
    if not value:
        return None
    value = value.strip()
    try:
        if len(value) == 4 and value.isdigit():
            return date(int(value), 1, 1)
        if "-" in value:
            parts = value.split("-")
            year = int(parts[0])
            month = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
            return date(year, month, 1)
    except (ValueError, IndexError):
        return None
    return None


async def _get_or_create_skill(db: AsyncSession, raw_name: str, category: str | None) -> Skill:
    canonical = normalize_skill_name(raw_name)
    normalized = normalize_text(canonical)
    result = await db.execute(select(Skill).where(Skill.normalized_name == normalized))
    skill = result.scalars().first()
    if skill is None:
        skill = Skill(name=canonical, normalized_name=normalized, category=category)
        db.add(skill)
        await db.flush()
    return skill


async def apply_extracted_profile(
    db: AsyncSession, *, candidate: Candidate, profile: CandidateProfile
) -> None:
    # Only overwrite fields the extraction actually found - never blank out
    # something a previous resume version already established.
    if profile.personal.name:
        candidate.name = profile.personal.name
    if profile.personal.email:
        candidate.email = profile.personal.email
    if profile.personal.phone:
        candidate.phone = profile.personal.phone
    if profile.personal.location:
        candidate.location = profile.personal.location
    if profile.links.linkedin:
        candidate.linkedin_url = profile.links.linkedin
    if profile.links.github:
        candidate.github_url = profile.links.github
    if profile.links.portfolio:
        candidate.portfolio_url = profile.links.portfolio
    if profile.total_years_experience is not None:
        candidate.total_years_experience = profile.total_years_experience
    if profile.experience:
        # Most recent experience entry becomes current_title/current_company
        current = next((e for e in profile.experience if e.is_current), profile.experience[0])
        candidate.current_title = current.title or candidate.current_title
        candidate.current_company = current.company or candidate.current_company

    for exp in profile.experience:
        start = _parse_year(exp.start_date)
        end = _parse_year(exp.end_date) if not exp.is_current else None
        years = None
        if start:
            end_for_calc = end or date.today()
            years = round((end_for_calc - start).days / 365.25, 1)
        description = "\n".join(exp.responsibilities + exp.achievements) or None
        db.add(
            Experience(
                candidate_id=candidate.id,
                company=exp.company,
                title=exp.title,
                start_date=start,
                end_date=end,
                description=description,
                years=years,
            )
        )

    for edu in profile.education:
        db.add(
            Education(
                candidate_id=candidate.id,
                institution=edu.institution,
                degree=edu.degree,
                field=edu.field,
                start_year=edu.start_year,
                end_year=edu.end_year,
            )
        )

    for cert in profile.certifications:
        db.add(
            Certification(
                candidate_id=candidate.id,
                name=cert.name,
                issuer=cert.issuer,
                issue_date=_parse_year(cert.issue_date),
            )
        )

    for proj in profile.projects:
        db.add(
            Project(
                candidate_id=candidate.id,
                name=proj.name,
                description=proj.description,
                technologies=proj.technologies,
            )
        )

    for skill in profile.skills:
        skill_row = await _get_or_create_skill(db, skill.name, skill.category)
        existing = await db.execute(
            select(CandidateSkill).where(
                CandidateSkill.candidate_id == candidate.id, CandidateSkill.skill_id == skill_row.id
            )
        )
        if existing.scalars().first() is None:
            db.add(
                CandidateSkill(
                    candidate_id=candidate.id,
                    skill_id=skill_row.id,
                    years_experience=skill.years_experience,
                )
            )


async def add_recruiter_note(
    db: AsyncSession, *, candidate_id, user_id, note_text: str
) -> RecruiterNote:
    from app.services.audit_service import record_audit_log

    note = RecruiterNote(candidate_id=candidate_id, user_id=user_id, note=note_text)
    db.add(note)
    await db.flush()
    await record_audit_log(
        db, user_id=user_id, action="NOTE_ADDED", resource_type="candidate", resource_id=candidate_id
    )
    await db.commit()
    await db.refresh(note)
    return note
