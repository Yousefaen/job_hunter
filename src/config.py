"""Configuration management for Job Hunter."""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, field_validator


# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESUMES_DIR = DATA_DIR / "resumes"
CONFIG_DIR = PROJECT_ROOT / "config"
DATABASE_PATH = DATA_DIR / "job_hunter.db"


class SearchCriteria(BaseModel):
    """Job search criteria configuration."""

    target_roles: list[str] = Field(
        default_factory=lambda: [
            "Chief of Staff",
            "Business Operations",
            "BizOps",
            "Head of Business Operations",
            "Director of Operations",
        ],
        description="Target job titles to search for",
    )
    locations: list[str] = Field(
        default_factory=lambda: ["New York", "San Francisco Bay Area", "Remote"],
        description="Target locations",
    )
    excluded_locations: list[str] = Field(
        default_factory=lambda: ["Israel"],
        description="Locations to exclude from search",
    )
    experience_levels: list[str] = Field(
        default_factory=lambda: ["Mid-Senior level", "Director"],
        description="Target experience levels",
    )
    company_sizes: list[str] = Field(
        default_factory=lambda: [
            "1-10 employees",
            "11-50 employees",
            "51-200 employees",
        ],
        description="Target company sizes (proxy for startup stage)",
    )
    min_match_score: int = Field(
        default=60, ge=0, le=100, description="Minimum job match score (0-100)"
    )
    easy_apply_only: bool = Field(
        default=True, description="Only apply to Easy Apply jobs"
    )


class RateLimits(BaseModel):
    """Rate limiting configuration."""

    min_delay_seconds: int = Field(
        default=30, ge=5, description="Minimum delay between actions"
    )
    max_delay_seconds: int = Field(
        default=90, ge=10, description="Maximum delay between actions"
    )
    max_applications_per_day: int = Field(
        default=25, ge=1, description="Maximum applications per day"
    )
    max_searches_per_hour: int = Field(
        default=10, ge=1, description="Maximum searches per hour"
    )


class Settings(BaseModel):
    """Application settings."""

    # API Keys (loaded from environment)
    anthropic_api_key: Optional[str] = Field(
        default=None, description="Anthropic API key for Claude"
    )
    linkedin_email: Optional[str] = Field(
        default=None, description="LinkedIn email for login"
    )
    linkedin_password: Optional[str] = Field(
        default=None, description="LinkedIn password for login"
    )

    # Paths
    resume_path: Optional[str] = Field(
        default=None, description="Path to user's resume (PDF or JSON)"
    )
    database_path: str = Field(
        default=str(DATABASE_PATH), description="Path to SQLite database"
    )

    # Feature flags
    headless_browser: bool = Field(
        default=False, description="Run browser in headless mode"
    )
    dry_run: bool = Field(
        default=False, description="Simulate actions without submitting applications"
    )
    verbose: bool = Field(default=False, description="Enable verbose logging")

    # Search criteria
    search_criteria: SearchCriteria = Field(default_factory=SearchCriteria)

    # Rate limits
    rate_limits: RateLimits = Field(default_factory=RateLimits)

    @field_validator("anthropic_api_key", mode="before")
    @classmethod
    def load_anthropic_key(cls, v: Optional[str]) -> Optional[str]:
        """Load API key from environment if not provided."""
        return v or os.environ.get("ANTHROPIC_API_KEY")

    @field_validator("linkedin_email", mode="before")
    @classmethod
    def load_linkedin_email(cls, v: Optional[str]) -> Optional[str]:
        """Load LinkedIn email from environment if not provided."""
        return v or os.environ.get("LINKEDIN_EMAIL")

    @field_validator("linkedin_password", mode="before")
    @classmethod
    def load_linkedin_password(cls, v: Optional[str]) -> Optional[str]:
        """Load LinkedIn password from environment if not provided."""
        return v or os.environ.get("LINKEDIN_PASSWORD")


def load_yaml_config(path: Path) -> dict:
    """Load configuration from a YAML file.

    Args:
        path: Path to the YAML file.

    Returns:
        Dictionary with configuration values.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        yaml.YAMLError: If the file is invalid YAML.
    """
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def load_settings(
    settings_path: Optional[Path] = None,
    search_criteria_path: Optional[Path] = None,
) -> Settings:
    """Load settings from YAML files and environment variables.

    Args:
        settings_path: Path to settings.yaml (optional).
        search_criteria_path: Path to search_criteria.yaml (optional).

    Returns:
        Settings object with merged configuration.
    """
    config_data = {}

    # Load settings.yaml if it exists
    settings_file = settings_path or CONFIG_DIR / "settings.yaml"
    if settings_file.exists():
        config_data.update(load_yaml_config(settings_file))

    # Load search_criteria.yaml if it exists
    criteria_file = search_criteria_path or CONFIG_DIR / "search_criteria.yaml"
    if criteria_file.exists():
        criteria_data = load_yaml_config(criteria_file)
        config_data["search_criteria"] = criteria_data

    return Settings(**config_data)


def ensure_directories() -> None:
    """Ensure all required directories exist."""
    DATA_DIR.mkdir(exist_ok=True)
    RESUMES_DIR.mkdir(exist_ok=True)
    CONFIG_DIR.mkdir(exist_ok=True)


# Ensure directories exist on import
ensure_directories()
