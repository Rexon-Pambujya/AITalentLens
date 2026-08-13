"""
Strict extraction schemas (section 60).

These are the ONLY shapes an LLM's resume-extraction output is allowed to
take. `model_validate_json` on `CandidateProfile` is what stands between
"whatever the model felt like returning" and anything touching the
database - if a field doesn't fit here, it's dropped, not coerced.

Every field is Optional with a safe default: partial/messy resumes should
extract what they can rather than fail the whole document (section 62).
"""
from pydantic import BaseModel, Field, model_validator


class _CoercesNullLists(BaseModel):
    """LLM structured output frequently emits `null` for a field it has
    nothing to report (e.g. `"responsibilities": null`, `"personal": null`)
    rather than omitting the key or emitting `[]`/`{}`. Pydantic's
    `default_factory` only kicks in when the key is ABSENT, not when it's
    present as null, so every list/nested-model field below would otherwise
    hard-fail validation on that - extremely common - LLM behavior. Coerces
    null -> the field's own default for any field that declares one."""

    @model_validator(mode="before")
    @classmethod
    def _null_to_default(cls, data):
        if not isinstance(data, dict):
            return data
        for name, field in cls.model_fields.items():
            if data.get(name) is None and name in data and field.default_factory is not None:
                data[name] = field.default_factory()
        return data


class ExtractedLinks(_CoercesNullLists):
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None
    other: list[str] = Field(default_factory=list)


class ExtractedPersonalInfo(_CoercesNullLists):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None


class ExtractedSkill(_CoercesNullLists):
    name: str
    category: str | None = Field(
        default=None, description="e.g. programming_language, framework, database, cloud, ml_ai, devops, tool, soft_skill"
    )
    years_experience: float | None = None


class ExtractedExperience(_CoercesNullLists):
    company: str | None = None
    title: str | None = None
    start_date: str | None = Field(default=None, description="ISO-ish, e.g. '2021-03' or '2021'")
    end_date: str | None = Field(default=None, description="null/omitted means current role")
    is_current: bool = False
    responsibilities: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)


class ExtractedEducation(_CoercesNullLists):
    institution: str | None = None
    degree: str | None = None
    field: str | None = None
    start_year: int | None = None
    end_year: int | None = None


class ExtractedCertification(_CoercesNullLists):
    name: str
    issuer: str | None = None
    issue_date: str | None = None


class ExtractedProject(_CoercesNullLists):
    name: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    impact: str | None = None


class ExtractedAchievement(_CoercesNullLists):
    description: str
    category: str | None = Field(default=None, description="award, publication, metric, other")


class CandidateProfile(_CoercesNullLists):
    """Top-level schema an LLM extraction call must conform to. See
    app/ai/prompts/resume_extraction.py for the accompanying system prompt,
    and app/extraction/resume_extractor.py for how this is validated and
    persisted."""

    personal: ExtractedPersonalInfo = Field(default_factory=ExtractedPersonalInfo)
    summary: str | None = None
    skills: list[ExtractedSkill] = Field(default_factory=list)
    experience: list[ExtractedExperience] = Field(default_factory=list)
    education: list[ExtractedEducation] = Field(default_factory=list)
    certifications: list[ExtractedCertification] = Field(default_factory=list)
    projects: list[ExtractedProject] = Field(default_factory=list)
    achievements: list[ExtractedAchievement] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    links: ExtractedLinks = Field(default_factory=ExtractedLinks)
    total_years_experience: float | None = None


# --- Job Description extraction schema (section 9) ---


class ExtractedRequirement(_CoercesNullLists):
    skill: str
    importance: float = Field(default=1.0, ge=0.0, le=1.0)
    required: bool = True
    minimum_years: float | None = None


class ExtractedEducationRequirement(_CoercesNullLists):
    degree_level: str = Field(description="e.g. bachelors, masters, phd, none")
    field: str | None = None
    required: bool = True


class JobProfile(_CoercesNullLists):
    """Output schema for JD analysis (POST /jobs/{id}/analyze). The
    recruiter reviews and can edit every field here before it's saved
    (section 45: 'AI should assist recruiters, not silently make
    assumptions')."""

    title: str | None = None
    seniority: str | None = Field(default=None, description="e.g. junior, mid, senior, staff, principal")
    department: str | None = None
    required_skills: list[ExtractedRequirement] = Field(default_factory=list)
    preferred_skills: list[ExtractedRequirement] = Field(default_factory=list)
    min_experience_years: float | None = None
    preferred_experience_years: float | None = None
    education_requirements: list[ExtractedEducationRequirement] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    industry: str | None = None
    tools: list[str] = Field(default_factory=list)
    cloud_platforms: list[str] = Field(default_factory=list)
    programming_languages: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    employment_type: str | None = None
    ambiguous_requirements: list[str] = Field(
        default_factory=list,
        description="Requirements the model found unclear/underspecified - surfaced to the recruiter rather than silently guessed at.",
    )
