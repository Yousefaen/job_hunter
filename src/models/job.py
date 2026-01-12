"""Job posting data models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Job(BaseModel):
    """Job posting data model."""

    id: str = Field(..., description="Unique job identifier")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    description: str = Field(default="", description="Full job description")
    url: str = Field(default="", description="Job posting URL")

    # Company details
    company_size: Optional[str] = Field(None, description="Company size range")
    company_industry: Optional[str] = Field(None, description="Company industry")

    # Job details
    experience_level: Optional[str] = Field(None, description="Required experience level")
    job_type: Optional[str] = Field(None, description="Full-time, Part-time, Contract")
    salary_range: Optional[str] = Field(None, description="Salary range if available")

    # Application details
    easy_apply: bool = Field(default=False, description="LinkedIn Easy Apply available")
    remote: bool = Field(default=False, description="Remote position")

    # Metadata
    posted_date: Optional[str] = Field(None, description="When job was posted")
    scraped_at: datetime = Field(default_factory=datetime.now, description="When job was scraped")

    def is_remote(self) -> bool:
        """Check if job is remote based on location or flag."""
        if self.remote:
            return True
        location_lower = self.location.lower()
        return "remote" in location_lower


class JobMatch(BaseModel):
    """Job with match score and justification."""

    job: Job = Field(..., description="The job posting")
    score: int = Field(..., ge=0, le=100, description="Match score 0-100")
    justification: str = Field(default="", description="AI-generated match explanation")
    matched_skills: list[str] = Field(default_factory=list, description="Skills that matched")
    concerns: list[str] = Field(default_factory=list, description="Potential concerns or gaps")

    @property
    def score_category(self) -> str:
        """Get score category for display."""
        if self.score >= 80:
            return "excellent"
        elif self.score >= 60:
            return "good"
        else:
            return "poor"
