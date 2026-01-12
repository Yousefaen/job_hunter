"""Job posting data model."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class JobStatus(str, Enum):
    """Status of a job in the pipeline."""

    FOUND = "found"  # Job discovered
    FILTERED = "filtered"  # Passed keyword filter
    MATCHED = "matched"  # Passed LLM scoring
    APPLIED = "applied"  # Application submitted
    REJECTED = "rejected"  # Not a good match
    INTERVIEWING = "interviewing"  # In interview process
    OFFERED = "offered"  # Received offer
    CLOSED = "closed"  # Position closed


class Job(BaseModel):
    """Model for a job posting."""

    id: Optional[str] = None
    linkedin_job_id: str = Field(..., description="LinkedIn's job ID")
    title: str
    company: str
    company_linkedin_url: Optional[str] = None
    location: str
    description: str
    posted_date: Optional[datetime] = None

    # Job details
    employment_type: Optional[str] = None  # Full-time, Part-time, etc.
    experience_level: Optional[str] = None  # Entry, Mid-Senior, etc.
    company_size: Optional[str] = None  # "1-10", "11-50", etc.
    industry: Optional[str] = None

    # Application info
    easy_apply: bool = False
    application_url: Optional[str] = None

    # Matching metadata
    status: JobStatus = JobStatus.FOUND
    match_score: Optional[int] = Field(None, ge=0, le=100)
    match_reasoning: Optional[str] = None
    key_matches: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)

    # Timestamps
    found_at: datetime = Field(default_factory=_utc_now)
    matched_at: Optional[datetime] = None
    applied_at: Optional[datetime] = None

    model_config = ConfigDict(
        ser_json_timedelta="iso8601",
    )
