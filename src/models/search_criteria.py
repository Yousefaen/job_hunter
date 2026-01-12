"""Search criteria configuration model."""

from typing import Optional, Self
from pydantic import BaseModel, Field, model_validator


class SearchCriteria(BaseModel):
    """Configuration for job search preferences."""

    # Job titles to search for
    titles: list[str] = Field(
        default_factory=lambda: [
            "Chief of Staff",
            "Business Operations",
            "BizOps",
            "Head of Business Operations",
            "Director of Operations",
        ]
    )

    # Locations
    locations: list[str] = Field(
        default_factory=lambda: [
            "New York, NY",
            "New York City Metropolitan Area",
            "Palo Alto, CA",
            "San Francisco Bay Area",
            "Remote",
        ]
    )

    # Excluded locations
    excluded_locations: list[str] = Field(
        default_factory=lambda: ["Israel"]
    )

    # Excluded companies
    excluded_companies: list[str] = Field(default_factory=list)

    # Experience level
    experience_levels: list[str] = Field(
        default_factory=lambda: [
            "Mid-Senior level",
            "Senior level",
        ]
    )

    # Job type
    job_types: list[str] = Field(
        default_factory=lambda: ["Full-time"]
    )

    # Company size (proxy for startup stage)
    company_sizes: list[str] = Field(
        default_factory=lambda: [
            "1-10 employees",
            "11-50 employees",
            "51-200 employees",
        ]
    )

    # Date posted filter
    date_posted: str = "Past week"

    # Easy Apply only
    easy_apply_only: bool = True

    # Matching threshold
    min_match_score: int = Field(default=60, ge=0, le=100)

    # Keywords for initial filtering (optional)
    required_keywords: list[str] = Field(default_factory=list)
    excluded_keywords: list[str] = Field(default_factory=list)

    # Rate limiting
    max_applications_per_day: int = Field(default=25, ge=1)
    min_delay_between_applications: int = Field(default=30, ge=10)  # seconds
    max_delay_between_applications: int = Field(default=90, ge=30)  # seconds

    @model_validator(mode="after")
    def validate_delays(self) -> Self:
        """Ensure max_delay >= min_delay."""
        if self.max_delay_between_applications < self.min_delay_between_applications:
            raise ValueError(
                f"max_delay_between_applications ({self.max_delay_between_applications}) "
                f"must be >= min_delay_between_applications ({self.min_delay_between_applications})"
            )
        return self

    def is_company_excluded(self, company: str) -> bool:
        """Check if a company is in the exclusion list."""
        company_lower = company.lower()
        return any(exc.lower() in company_lower for exc in self.excluded_companies)
