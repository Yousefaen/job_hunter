"""Search criteria data model."""

from typing import Optional
from pydantic import BaseModel, Field


class SearchCriteria(BaseModel):
    """Job search criteria configuration."""

    # Job titles to search
    titles: list[str] = Field(
        default_factory=lambda: [
            "Chief of Staff",
            "Business Operations",
            "BizOps",
            "Head of Business Operations",
            "Director of Operations",
        ],
        description="Job titles to search for"
    )

    # Locations
    locations: list[str] = Field(
        default_factory=lambda: [
            "New York, NY",
            "San Francisco Bay Area",
            "Remote",
        ],
        description="Locations to search in"
    )

    # Experience levels
    experience_levels: list[str] = Field(
        default_factory=lambda: [
            "Mid-Senior level",
            "Senior level",
        ],
        description="Experience levels to filter"
    )

    # Company size filters
    company_sizes: list[str] = Field(
        default_factory=lambda: [
            "1-10 employees",
            "11-50 employees",
            "51-200 employees",
        ],
        description="Company size ranges (proxy for startup stage)"
    )

    # Date filter
    date_posted: str = Field(
        default="Past week",
        description="Date filter for job postings"
    )

    # Job type
    job_type: str = Field(
        default="Full-time",
        description="Job type filter"
    )

    # Easy Apply filter
    easy_apply_only: bool = Field(
        default=True,
        description="Only show Easy Apply jobs"
    )

    # Exclusions
    excluded_locations: list[str] = Field(
        default_factory=lambda: ["Israel"],
        description="Locations to exclude"
    )

    excluded_companies: list[str] = Field(
        default_factory=list,
        description="Companies to exclude"
    )

    excluded_keywords: list[str] = Field(
        default_factory=list,
        description="Keywords to exclude from job descriptions"
    )

    # Matching thresholds
    min_match_score: int = Field(
        default=60,
        ge=0,
        le=100,
        description="Minimum match score to show"
    )

    def to_search_query(self, title_index: int = 0) -> str:
        """Generate a LinkedIn search query string."""
        if title_index < len(self.titles):
            return self.titles[title_index]
        return self.titles[0] if self.titles else "Chief of Staff"

    def is_location_excluded(self, location: str) -> bool:
        """Check if a location should be excluded."""
        location_lower = location.lower()
        return any(
            excluded.lower() in location_lower
            for excluded in self.excluded_locations
        )

    def is_company_excluded(self, company: str) -> bool:
        """Check if a company should be excluded."""
        company_lower = company.lower()
        return any(
            excluded.lower() in company_lower
            for excluded in self.excluded_companies
        )
