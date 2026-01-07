"""Data models for job hunter application."""

from .job import Job, JobStatus
from .application import Application, ApplicationStatus
from .search_criteria import SearchCriteria

__all__ = [
    "Job",
    "JobStatus",
    "Application",
    "ApplicationStatus",
    "SearchCriteria",
]
