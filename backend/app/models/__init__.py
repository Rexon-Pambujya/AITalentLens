"""
Importing this module registers every mapped class on `Base.metadata`.
Alembic's env.py imports `Base` from here (indirectly via app.db.base) -
so any new model file MUST be added to this list or migrations will silently
ignore it.
"""
from app.db.base import Base  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.candidate import Candidate  # noqa: F401
from app.models.candidate_pipeline import CandidatePipeline  # noqa: F401
from app.models.certification import Certification  # noqa: F401
from app.models.education import Education  # noqa: F401
from app.models.experience import Experience  # noqa: F401
from app.models.job import Job, JobRequirement  # noqa: F401
from app.models.match import Match  # noqa: F401
from app.models.organization import Organization  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.recruiter_note import RecruiterNote  # noqa: F401
from app.models.resume import Resume, ResumeEmbedding  # noqa: F401
from app.models.skill import CandidateSkill, Skill  # noqa: F401
from app.models.user import User  # noqa: F401

__all__ = [
    "Base",
    "AuditLog",
    "Candidate",
    "CandidatePipeline",
    "Certification",
    "Education",
    "Experience",
    "Job",
    "JobRequirement",
    "Match",
    "Organization",
    "Project",
    "RecruiterNote",
    "Resume",
    "ResumeEmbedding",
    "CandidateSkill",
    "Skill",
    "User",
]
