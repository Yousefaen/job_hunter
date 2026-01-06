"""Search criteria model for LinkedIn job search configuration."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SearchCriteria(BaseModel):
    """
    Job search criteria and filters.

    Attributes:
        titles: List of job titles to search for
        locations: List of locations to search in
        experience_levels: Desired experience levels
        job_types: Employment types (Full-time, Part-time, etc.)
        company_sizes: Company size brackets (proxy for startup stage)
        date_posted: Recency filter (e.g., "Past week", "Past month")
        easy_apply_only: Only show Easy Apply jobs
        excluded_locations: Locations to exclude (e.g., specific countries/cities)
        excluded_companies: Company names to exclude
        min_match_score: Minimum acceptable match score (0-100)
        keywords_required: Keywords that must appear in job description
        keywords_excluded: Keywords that disqualify a job
    """

    # Core search parameters
    titles: list[str] = Field(
        ...,
        description="Job titles to search for",
        min_length=1
    )
    locations: list[str] = Field(
        ...,
        description="Locations to search in",
        min_length=1
    )

    # Experience and job type filters
    experience_levels: list[str] = Field(
        default_factory=lambda: ["Mid-Senior level", "Senior level"],
        description="Experience levels to filter by"
    )
    job_types: list[str] = Field(
        default_factory=lambda: ["Full-time"],
        description="Job types to filter by"
    )

    # Company filters
    company_sizes: list[str] = Field(
        default_factory=lambda: [
            "1-10 employees",
            "11-50 employees",
            "51-200 employees",
        ],
        description="Company sizes (proxy for seed to Series A)"
    )

    # Recency and Easy Apply
    date_posted: str = Field(
        default="Past week",
        description="How recently job was posted"
    )
    easy_apply_only: bool = Field(
        default=True,
        description="Only show Easy Apply jobs"
    )

    # Exclusions
    excluded_locations: list[str] = Field(
        default_factory=list,
        description="Locations to exclude from search"
    )
    excluded_companies: list[str] = Field(
        default_factory=list,
        description="Company names to exclude"
    )

    # Matching thresholds
    min_match_score: float = Field(
        default=60.0,
        ge=0.0,
        le=100.0,
        description="Minimum match score to apply (0-100)"
    )

    # Keyword filters
    keywords_required: list[str] = Field(
        default_factory=list,
        description="Keywords that must appear in job"
    )
    keywords_excluded: list[str] = Field(
        default_factory=list,
        description="Keywords that disqualify a job"
    )

    # Rate limiting and safety
    max_applications_per_day: int = Field(
        default=25,
        ge=1,
        le=100,
        description="Maximum number of applications per day"
    )
    min_delay_between_actions: int = Field(
        default=30,
        ge=10,
        le=300,
        description="Minimum delay between actions in seconds"
    )
    max_delay_between_actions: int = Field(
        default=90,
        ge=30,
        le=600,
        description="Maximum delay between actions in seconds"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "titles": [
                    "Chief of Staff",
                    "Business Operations",
                    "BizOps",
                    "Head of Business Operations",
                    "Director of Operations"
                ],
                "locations": [
                    "New York, NY",
                    "Palo Alto, CA",
                    "San Francisco Bay Area",
                    "Remote"
                ],
                "experience_levels": ["Mid-Senior level", "Senior level"],
                "job_types": ["Full-time"],
                "company_sizes": [
                    "1-10 employees",
                    "11-50 employees",
                    "51-200 employees"
                ],
                "date_posted": "Past week",
                "easy_apply_only": True,
                "excluded_locations": ["Israel"],
                "excluded_companies": [],
                "min_match_score": 60.0,
                "keywords_required": [],
                "keywords_excluded": ["senior engineer", "software developer"],
                "max_applications_per_day": 25,
                "min_delay_between_actions": 30,
                "max_delay_between_actions": 90
            }
        }
    )

    @model_validator(mode="after")
    def validate_delays(self) -> "SearchCriteria":
        """Ensure min_delay is less than max_delay."""
        if self.min_delay_between_actions >= self.max_delay_between_actions:
            raise ValueError(
                f"min_delay_between_actions ({self.min_delay_between_actions}) "
                f"must be less than max_delay_between_actions ({self.max_delay_between_actions})"
            )
        return self

    def should_exclude_location(self, location: str) -> bool:
        """
        Check if a location should be excluded.

        Args:
            location: Job location string

        Returns:
            True if location matches any exclusion pattern
        """
        location_lower = location.lower()
        return any(
            excluded.lower() in location_lower
            for excluded in self.excluded_locations
        )

    def should_exclude_company(self, company: str) -> bool:
        """
        Check if a company should be excluded.

        Args:
            company: Company name

        Returns:
            True if company matches any exclusion pattern
        """
        company_lower = company.lower()
        return any(
            excluded.lower() in company_lower
            for excluded in self.excluded_companies
        )

    def has_required_keywords(self, text: str) -> bool:
        """
        Check if text contains all required keywords.

        Args:
            text: Text to search (usually job description)

        Returns:
            True if all required keywords are present (or no requirements)
        """
        if not self.keywords_required:
            return True

        text_lower = text.lower()
        return all(
            keyword.lower() in text_lower
            for keyword in self.keywords_required
        )

    def has_excluded_keywords(self, text: str) -> bool:
        """
        Check if text contains any excluded keywords.

        Args:
            text: Text to search (usually job description)

        Returns:
            True if any excluded keyword is present
        """
        if not self.keywords_excluded:
            return False

        text_lower = text.lower()
        return any(
            keyword.lower() in text_lower
            for keyword in self.keywords_excluded
        )

    def __str__(self) -> str:
        """String representation of search criteria."""
        return (
            f"SearchCriteria(titles={len(self.titles)}, "
            f"locations={len(self.locations)}, "
            f"min_score={self.min_match_score})"
        )
