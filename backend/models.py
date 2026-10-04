from datetime import datetime

from sqlalchemy import Column, DateTime, Index, Integer, Text

from database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    candidate_name = Column(
        Text,
        nullable=True
    )

    resume_filename = Column(
        Text,
        nullable=False
    )

    job_description = Column(
        Text,
        nullable=True
    )

    resume_text = Column(
        Text,
        nullable=False
    )

    analysis_json = Column(
        Text,
        nullable=False
    )

    # sha256 of normalized resume_text / job_description, used to
    # detect duplicate screenings (same resume + same JD) instead of
    # silently creating a new record and re-calling the LLM.
    resume_hash = Column(
        Text,
        nullable=True,
        index=True
    )

    job_hash = Column(
        Text,
        nullable=True,
        index=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    __table_args__ = (
        Index("ix_candidates_resume_job_hash", "resume_hash", "job_hash"),
    )
