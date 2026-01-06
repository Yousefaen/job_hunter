"""Configuration management for job hunter application."""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from job_hunter.models import SearchCriteria


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and config files.

    Environment variables take precedence over config file values.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # API Keys and Credentials
    anthropic_api_key: str = Field(..., description="Anthropic API key for Claude")
    linkedin_email: str = Field(..., description="LinkedIn account email")
    linkedin_password: str = Field(..., description="LinkedIn account password")

    # Paths
    database_path: Path = Field(
        default=Path("data/job_hunter.db"),
        description="Path to SQLite database"
    )
    resume_dir: Path = Field(
        default=Path("data/resumes"),
        description="Directory containing user resumes"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_file: Optional[Path] = Field(
        default=None,
        description="Optional log file path"
    )

    # Browser settings
    headless: bool = Field(
        default=False,
        description="Run browser in headless mode"
    )
    browser_timeout: int = Field(
        default=30000,
        ge=5000,
        le=120000,
        description="Browser timeout in milliseconds"
    )

    # Rate limiting
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting for safety"
    )

    # Dry run mode
    dry_run: bool = Field(
        default=False,
        description="Preview actions without actually applying"
    )

    def __init__(self, **kwargs):
        """Initialize settings and ensure directories exist."""
        super().__init__(**kwargs)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.resume_dir.mkdir(parents=True, exist_ok=True)

        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)


class Config:
    """Configuration loader for application settings and search criteria."""

    def __init__(self, config_dir: Path = Path("config")):
        """
        Initialize configuration loader.

        Args:
            config_dir: Directory containing configuration YAML files
        """
        self.config_dir = config_dir
        self._settings: Optional[Settings] = None
        self._search_criteria: Optional[SearchCriteria] = None

    def load_settings(self) -> Settings:
        """
        Load application settings from environment and config file.

        Returns:
            Settings object with loaded configuration

        Raises:
            ValueError: If required settings are missing
        """
        if self._settings is None:
            settings_path = self.config_dir / "settings.yaml"

            # Load from YAML if exists
            yaml_config = {}
            if settings_path.exists():
                with open(settings_path, "r") as f:
                    yaml_config = yaml.safe_load(f) or {}

            # Environment variables override YAML
            self._settings = Settings(**yaml_config)

        return self._settings

    def load_search_criteria(self) -> SearchCriteria:
        """
        Load job search criteria from configuration file.

        Returns:
            SearchCriteria object with search parameters

        Raises:
            FileNotFoundError: If search_criteria.yaml not found
            ValueError: If configuration is invalid
        """
        if self._search_criteria is None:
            criteria_path = self.config_dir / "search_criteria.yaml"

            if not criteria_path.exists():
                raise FileNotFoundError(
                    f"Search criteria file not found: {criteria_path}\n"
                    "Please create config/search_criteria.yaml with your search parameters."
                )

            with open(criteria_path, "r") as f:
                criteria_data = yaml.safe_load(f)

            self._search_criteria = SearchCriteria(**criteria_data)

        return self._search_criteria

    def save_search_criteria(self, criteria: SearchCriteria) -> None:
        """
        Save search criteria to YAML file.

        Args:
            criteria: SearchCriteria object to save
        """
        criteria_path = self.config_dir / "search_criteria.yaml"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        with open(criteria_path, "w") as f:
            yaml.dump(criteria.model_dump(), f, default_flow_style=False, sort_keys=False)

        self._search_criteria = criteria

    def reload(self) -> None:
        """Reload all configuration from disk."""
        self._settings = None
        self._search_criteria = None

    @property
    def settings(self) -> Settings:
        """Get settings (lazy load if needed)."""
        return self.load_settings()

    @property
    def search_criteria(self) -> SearchCriteria:
        """Get search criteria (lazy load if needed)."""
        return self.load_search_criteria()


# Global config instance
_config: Optional[Config] = None


def get_config(config_dir: Path = Path("config")) -> Config:
    """
    Get global configuration instance (singleton pattern).

    Args:
        config_dir: Directory containing configuration files

    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config(config_dir)
    return _config


def reset_config() -> None:
    """Reset global configuration instance (useful for testing)."""
    global _config
    _config = None
