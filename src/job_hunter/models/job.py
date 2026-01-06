"""Job posting model for LinkedIn job listings."""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class Job(BaseModel):
    """
    Represents a LinkedIn job posting.

    Attributes:
        job_id: Unique LinkedIn job identifier
        title: Job title/position name
        company: Company name
        location: Job location (city, state, or "Remote")
        description: Full job description text
        posted_date: When the job was posted
        url: Direct URL to the job posting
        easy_apply: Whether job supports Easy Apply
        company_size: Number of employees (e.g., "11-50 employees")
        experience_level: Required experience level (e.g., "Mid-Senior level")
        job_type: Employment type (e.g., "Full-time")
        match_score: Job-resume match score (0-100) from LLM
        match_reasoning: Explanation for the match score
        keywords: Extracted keywords from job description
        created_at: Timestamp when job was added to database
        updated_at: Timestamp when job was last updated
    """

    job_id: str = Field(..., description="LinkedIn job ID")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    description: str = Field(..., description="Full job description")
    posted_date: Optional[str] = Field(None, description="Date posted (e.g., '2 days ago')")
    url: HttpUrl = Field(..., description="Job posting URL")

    # Job metadata
    easy_apply: bool = Field(default=False, description="Supports Easy Apply")
    company_size: Optional[str] = Field(None, description="Company size bracket")
    experience_level: Optional[str] = Field(None, description="Required experience level")
    job_type: Optional[str] = Field(None, description="Job type (Full-time, Part-time, etc.)")

    # Matching data
    match_score: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Match score from LLM (0-100)"
    )
    match_reasoning: Optional[str] = Field(None, description="Explanation for match score")
    keywords: list[str] = Field(default_factory=list, description="Extracted keywords")

    # Timestamps
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "3789456123",
                "title": "Chief of Staff",
                "company": "Acme Startup Inc",
                "location": "New York, NY",
                "description": "We're seeking an experienced Chief of Staff...",
                "posted_date": "2 days ago",
                "url": "https://www.linkedin.com/jobs/view/3789456123",
                "easy_apply": True,
                "company_size": "11-50 employees",
                "experience_level": "Mid-Senior level",
                "job_type": "Full-time",
                "match_score": 85.5,
                "match_reasoning": "Strong match based on BizOps experience...",
                "keywords": ["chief of staff", "business operations", "startup"],
            }
        }
    )

    def is_seed_to_series_a(self) -> bool:
        """
        Check if company size indicates seed to Series A stage.

        Returns:
            True if company size is 1-200 employees
        """
        if not self.company_size:
            return False

        seed_series_a_sizes = [
            "1-10 employees",
            "11-50 employees",
            "51-200 employees",
        ]
        return self.company_size in seed_series_a_sizes

    def meets_minimum_score(self, min_score: float = 60.0) -> bool:
        """
        Check if job meets minimum match score threshold.

        Args:
            min_score: Minimum acceptable match score (default: 60.0)

        Returns:
            True if match_score >= min_score, False otherwise
        """
        if self.match_score is None:
            return False
        return self.match_score >= min_score

    def __str__(self) -> str:
        """String representation of the job."""
        return f"{self.title} at {self.company} ({self.location})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"Job(job_id='{self.job_id}', title='{self.title}', "
            f"company='{self.company}', match_score={self.match_score})"
        )
