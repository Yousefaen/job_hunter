"""Application tracking data model."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class ApplicationStatus(str, Enum):
    """Status of a job application."""

    PENDING = "pending"
    SUBMITTED = "submitted"
    REJECTED = "rejected"
    INTERVIEWING = "interviewing"
    OFFERED = "offered"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class Application(BaseModel):
    """Model for tracking job applications."""

    id: Optional[str] = None
    job_id: str  # Foreign key to Job

    # Application details
    status: ApplicationStatus = ApplicationStatus.PENDING
    submitted_at: Optional[datetime] = None

    # Form responses
    custom_questions: Dict[str, str] = Field(default_factory=dict)
    cover_letter: Optional[str] = None

    # Tracking
    follow_up_date: Optional[datetime] = None
    notes: str = ""

    # Interview tracking
    interviews: list[Dict[str, Any]] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)

    model_config = ConfigDict(
        ser_json_timedelta="iso8601",
    )
