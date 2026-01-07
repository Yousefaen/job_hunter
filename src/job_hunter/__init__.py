"""Job Hunter - Intelligent LinkedIn job application agent."""

__version__ = "0.1.0"

from job_hunter.config import Config, Settings, get_config
from job_hunter.models import Application, ApplicationStatus, Job, SearchCriteria
from job_hunter.storage import Database

__all__ = [
    "__version__",
    "Application",
    "ApplicationStatus",
    "Config",
    "Database",
    "Job",
    "SearchCriteria",
    "Settings",
    "get_config",
]
