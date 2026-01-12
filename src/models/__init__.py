"""Data models for job hunter."""

from .job import Job, JobMatch
from .search_criteria import SearchCriteria
from .application import Application, ApplicationStatus

__all__ = [
    "Job",
    "JobMatch",
    "SearchCriteria",
    "Application",
    "ApplicationStatus",
]
