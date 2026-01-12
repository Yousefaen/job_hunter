"""Pytest configuration and fixtures."""

import os
from datetime import date

import pytest

from src.models.job import Job
from src.models.search_criteria import SearchCriteria
from src.resume.profile import UserProfile, Experience, Education


@pytest.fixture
def sample_profile() -> UserProfile:
    """Create a sample user profile for testing."""
    return UserProfile(
        full_name="Jane Doe",
        email="jane.doe@example.com",
        phone="+1-555-0100",
        location="New York, NY",
        linkedin_url="https://linkedin.com/in/janedoe",
        summary="Experienced business operations leader with 8+ years in scaling startups. "
        "Expertise in strategic planning, cross-functional collaboration, and operational excellence.",
        headline="Chief of Staff | Business Operations Leader",
        skills=[
            "Strategic Planning",
            "Business Operations",
            "Cross-functional Leadership",
            "OKRs",
            "Project Management",
            "Data Analysis",
        ],
        technical_skills=[
            "SQL",
            "Python",
            "Tableau",
            "Salesforce",
        ],
        experiences=[
            Experience(
                company="TechStartup Inc",
                title="Chief of Staff",
                location="New York, NY",
                start_date=date(2020, 1, 1),
                current=True,
                description="Led strategic initiatives and cross-functional operations for 50-person startup",
                achievements=[
                    "Implemented OKR framework across all departments",
                    "Reduced operational costs by 30% through process optimization",
                ],
            ),
            Experience(
                company="GrowthCo",
                title="Business Operations Manager",
                location="San Francisco, CA",
                start_date=date(2017, 6, 1),
                end_date=date(2019, 12, 31),
                description="Managed operations and analytics for Series A SaaS company",
                achievements=[
                    "Built data infrastructure supporting $10M ARR growth",
                ],
            ),
        ],
        education=[
            Education(
                institution="Stanford University",
                degree="MBA",
                field_of_study="Business Administration",
                start_date=date(2015, 9, 1),
                end_date=date(2017, 6, 1),
            ),
        ],
    )


@pytest.fixture
def sample_criteria() -> SearchCriteria:
    """Create sample search criteria."""
    return SearchCriteria(
        titles=[
            "Chief of Staff",
            "Business Operations",
            "BizOps",
        ],
        locations=[
            "New York, NY",
            "San Francisco, CA",
            "Remote",
        ],
        excluded_locations=["Israel"],
        company_sizes=[
            "1-10 employees",
            "11-50 employees",
            "51-200 employees",
        ],
        min_match_score=60,
    )


@pytest.fixture
def good_match_job() -> Job:
    """Create a job that should match well."""
    return Job(
        linkedin_job_id="12345",
        title="Chief of Staff",
        company="Awesome Startup",
        location="New York, NY",
        description="""
        We're seeking a Chief of Staff to work directly with our CEO at our Seed-stage startup.

        Responsibilities:
        - Lead strategic planning and OKR implementation
        - Coordinate cross-functional projects
        - Drive operational excellence
        - Support fundraising efforts

        Requirements:
        - 5+ years in business operations or Chief of Staff roles
        - Experience at early-stage startups (Seed to Series A)
        - Strong analytical and project management skills
        - SQL and data analysis experience preferred

        Our startup is a 30-person team building the future of B2B SaaS.
        """,
        company_size="11-50 employees",
        experience_level="Mid-Senior level",
        easy_apply=True,
    )


@pytest.fixture
def poor_match_job() -> Job:
    """Create a job that should not match well."""
    return Job(
        linkedin_job_id="67890",
        title="Software Engineer",
        company="BigCorp",
        location="Seattle, WA",
        description="""
        Looking for a Senior Software Engineer to work on backend systems.

        Requirements:
        - 10+ years of Java development
        - Experience with distributed systems
        - Deep knowledge of algorithms and data structures

        We're a 5000-person enterprise software company.
        """,
        company_size="1001-5000 employees",
        experience_level="Senior level",
        easy_apply=False,
    )


@pytest.fixture
def excluded_location_job() -> Job:
    """Create a job in an excluded location."""
    return Job(
        linkedin_job_id="99999",
        title="Chief of Staff",
        company="Tech Co",
        location="Tel Aviv, Israel",
        description="Chief of Staff role at a growing startup.",
        company_size="11-50 employees",
        easy_apply=True,
    )


@pytest.fixture
def mock_api_key(monkeypatch) -> None:
    """Mock API key environment variable."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key-12345")
