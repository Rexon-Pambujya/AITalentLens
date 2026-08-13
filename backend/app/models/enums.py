import enum


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    RECRUITER = "RECRUITER"
    HIRING_MANAGER = "HIRING_MANAGER"


class JobStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ANALYZING = "ANALYZING"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class ResumeParsedStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    EXTRACTED = "EXTRACTED"
    EMBEDDED = "EMBEDDED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DUPLICATE = "DUPLICATE"


class PipelineStatus(str, enum.Enum):
    NEW = "NEW"
    SCREENING = "SCREENING"
    SHORTLISTED = "SHORTLISTED"
    INTERVIEW = "INTERVIEW"
    OFFER = "OFFER"
    HIRED = "HIRED"
    REJECTED = "REJECTED"


class RecommendationLabel(str, enum.Enum):
    STRONG_MATCH = "STRONG_MATCH"
    GOOD_MATCH = "GOOD_MATCH"
    MODERATE_MATCH = "MODERATE_MATCH"
    NOT_SUITABLE = "NOT_SUITABLE"


class SkillSource(str, enum.Enum):
    RESUME_EXTRACTION = "RESUME_EXTRACTION"
    RECRUITER_ADDED = "RECRUITER_ADDED"
    INFERRED = "INFERRED"
