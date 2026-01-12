"""Data models for job hunting application."""

from job_hunter.models.application import Application, ApplicationStatus
from job_hunter.models.job import Job
from job_hunter.models.search_criteria import SearchCriteria

__all__ = [
    "Application",
    "ApplicationStatus",
    "Job",
    "SearchCriteria",
]
