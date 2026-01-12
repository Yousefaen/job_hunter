"""Application tracking data model."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ApplicationStatus(str, Enum):
    """Status of a job application."""

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    FAILED = "failed"
    SKIPPED = "skipped"
    VIEWED = "viewed"
    REJECTED = "rejected"
    INTERVIEW = "interview"


class Application(BaseModel):
    """Job application record."""

    id: str = Field(..., description="Unique application identifier")
    job_id: str = Field(..., description="Associated job ID")
    job_title: str = Field(..., description="Job title for display")
    company: str = Field(..., description="Company name")

    # Status tracking
    status: ApplicationStatus = Field(
        default=ApplicationStatus.QUEUED,
        description="Current application status"
    )

    # Match info
    match_score: int = Field(default=0, description="Match score when applied")

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When application was queued"
    )
    submitted_at: Optional[datetime] = Field(
        None,
        description="When application was submitted"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Last status update"
    )

    # Additional info
    notes: str = Field(default="", description="Notes about the application")
    error_message: Optional[str] = Field(None, description="Error if failed")

    # Custom questions answered
    questions_answered: list[dict] = Field(
        default_factory=list,
        description="Custom questions and answers"
    )

    def mark_submitted(self) -> None:
        """Mark application as submitted."""
        self.status = ApplicationStatus.SUBMITTED
        self.submitted_at = datetime.now()
        self.updated_at = datetime.now()

    def mark_failed(self, error: str) -> None:
        """Mark application as failed."""
        self.status = ApplicationStatus.FAILED
        self.error_message = error
        self.updated_at = datetime.now()

    def mark_skipped(self, reason: str) -> None:
        """Mark application as skipped."""
        self.status = ApplicationStatus.SKIPPED
        self.notes = reason
        self.updated_at = datetime.now()
