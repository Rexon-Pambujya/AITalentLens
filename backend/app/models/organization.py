from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class Organization(Base, UUIDPKMixin, TimestampMixin):
    """The tenant boundary. Every recruiter-facing entity hangs off an
    organization, either directly or transitively (see section 31,
    Multi-Tenancy)."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="organization")
    jobs: Mapped[list["Job"]] = relationship(back_populates="organization")
    candidates: Mapped[list["Candidate"]] = relationship(back_populates="organization")
