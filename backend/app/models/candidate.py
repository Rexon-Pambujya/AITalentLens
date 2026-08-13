import uuid

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UpdatedAtMixin, UUIDPKMixin


class Candidate(Base, UUIDPKMixin, TimestampMixin, UpdatedAtMixin):
    """A person. One candidate can have multiple resumes (re-uploads,
    duplicate detection merges resumes onto a single candidate) and can be
    matched against many jobs."""

    __tablename__ = "candidates"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(50))
    location: Mapped[str | None] = mapped_column(String(255))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    github_url: Mapped[str | None] = mapped_column(String(500))
    portfolio_url: Mapped[str | None] = mapped_column(String(500))
    total_years_experience: Mapped[float | None] = mapped_column(Float)
    current_title: Mapped[str | None] = mapped_column(String(255))
    current_company: Mapped[str | None] = mapped_column(String(255))

    organization: Mapped["Organization"] = relationship(back_populates="candidates")
    resumes: Mapped[list["Resume"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    experiences: Mapped[list["Experience"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    educations: Mapped[list["Education"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    certifications: Mapped[list["Certification"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
