"""Application record model for tracking job applications."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class ApplicationStatus(str, Enum):
    """Application status values."""
    PENDING = "pending"           # Ready to apply
    APPLYING = "applying"         # Application in progress
    SUBMITTED = "submitted"       # Successfully submitted
    FAILED = "failed"            # Application failed
    REJECTED = "rejected"        # Rejected by company
    INTERVIEWING = "interviewing" # In interview process
    OFFERED = "offered"          # Received job offer
    ACCEPTED = "accepted"        # Accepted job offer
    DECLINED = "declined"        # Declined to proceed
    WITHDRAWN = "withdrawn"      # Withdrew application


class Application(BaseModel):
    """
    Represents a job application record.

    Attributes:
        application_id: Unique application identifier
        job_id: Reference to Job.job_id
        status: Current application status
        applied_at: Timestamp when application was submitted
        updated_at: Timestamp when status was last updated
        error_message: Error details if application failed
        custom_questions: Questions asked during application
        custom_answers: Answers provided to custom questions
        notes: User notes about the application
        follow_up_date: Optional reminder date for follow-up
    """

    application_id: Optional[str] = Field(None, description="Unique application ID")
    job_id: str = Field(..., description="Reference to job posting")

    # Status tracking
    status: ApplicationStatus = Field(
        default=ApplicationStatus.PENDING,
        description="Current application status"
    )

    # Timestamps
    applied_at: Optional[datetime] = Field(
        None,
        description="When application was submitted"
    )
    updated_at: datetime = Field(
        default_factory=_utc_now,
        description="Last status update"
    )

    # Application details
    error_message: Optional[str] = Field(
        None,
        description="Error details if application failed"
    )
    custom_questions: dict[str, str] = Field(
        default_factory=dict,
        description="Custom questions asked (key: question_id, value: question_text)"
    )
    custom_answers: dict[str, str] = Field(
        default_factory=dict,
        description="Answers to custom questions (key: question_id, value: answer)"
    )

    # User notes and follow-up
    notes: str = Field(
        default="",
        description="User notes about the application"
    )
    follow_up_date: Optional[datetime] = Field(
        None,
        description="Reminder date for follow-up"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "application_id": "app_123456",
                "job_id": "3789456123",
                "status": "submitted",
                "applied_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "error_message": None,
                "custom_questions": {
                    "q1": "Why are you interested in this role?",
                    "q2": "What's your salary expectation?"
                },
                "custom_answers": {
                    "q1": "I'm passionate about business operations...",
                    "q2": "$150,000 - $180,000"
                },
                "notes": "Seems like a great fit, company in Series A",
                "follow_up_date": "2024-01-22T00:00:00Z"
            }
        }
    )

    def mark_as_submitted(self) -> None:
        """Mark application as successfully submitted."""
        self.status = ApplicationStatus.SUBMITTED
        self.applied_at = _utc_now()
        self.updated_at = _utc_now()
        self.error_message = None

    def mark_as_failed(self, error: str) -> None:
        """
        Mark application as failed with error message.

        Args:
            error: Error message describing why application failed
        """
        self.status = ApplicationStatus.FAILED
        self.updated_at = _utc_now()
        self.error_message = error

    def update_status(self, new_status: ApplicationStatus, notes: str = "") -> None:
        """
        Update application status.

        Args:
            new_status: New status value
            notes: Optional notes about the status change
        """
        self.status = new_status
        self.updated_at = _utc_now()
        if notes:
            existing = self.notes.strip()
            self.notes = f"{existing}\n{notes}".strip() if existing else notes

    def add_custom_qa(self, question_id: str, question: str, answer: str) -> None:
        """
        Add a custom question and answer.

        Args:
            question_id: Unique identifier for the question
            question: The question text
            answer: The answer provided
        """
        self.custom_questions[question_id] = question
        self.custom_answers[question_id] = answer

    def is_active(self) -> bool:
        """
        Check if application is in an active state.

        Returns:
            True if status is pending, applying, submitted, or interviewing
        """
        active_statuses = {
            ApplicationStatus.PENDING,
            ApplicationStatus.APPLYING,
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.INTERVIEWING,
        }
        return self.status in active_statuses

    def is_completed(self) -> bool:
        """
        Check if application process is completed.

        Returns:
            True if status is accepted, declined, rejected, or withdrawn
        """
        completed_statuses = {
            ApplicationStatus.ACCEPTED,
            ApplicationStatus.DECLINED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        }
        return self.status in completed_statuses

    def __str__(self) -> str:
        """String representation of the application."""
        return f"Application(job_id={self.job_id}, status={self.status.value})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"Application(application_id='{self.application_id}', "
            f"job_id='{self.job_id}', status='{self.status.value}')"
        )
