"""Example usage of the job matching system."""

import os
from datetime import date

from src.agent.job_matcher import JobMatcher
from src.models.job import Job
from src.models.search_criteria import SearchCriteria
from src.resume.profile import UserProfile, Experience, Education


def create_sample_profile() -> UserProfile:
    """Create a sample user profile."""
    return UserProfile(
        full_name="Jane Doe",
        email="jane.doe@example.com",
        phone="+1-555-0100",
        location="New York, NY",
        summary=(
            "Experienced business operations leader with 8+ years scaling startups. "
            "Expert in strategic planning, cross-functional collaboration, and operational excellence."
        ),
        headline="Chief of Staff | Business Operations Leader",
        skills=[
            "Strategic Planning",
            "Business Operations",
            "Cross-functional Leadership",
            "OKRs & KPIs",
            "Project Management",
            "Data Analysis",
            "Process Optimization",
        ],
        technical_skills=[
            "SQL",
            "Python",
            "Tableau",
            "Salesforce",
            "Google Analytics",
        ],
        experiences=[
            Experience(
                company="TechStartup Inc",
                title="Chief of Staff",
                location="New York, NY",
                start_date=date(2020, 1, 1),
                current=True,
                description=(
                    "Lead strategic initiatives and cross-functional operations "
                    "for 50-person Series A SaaS startup."
                ),
                achievements=[
                    "Implemented OKR framework across all departments, improving goal alignment by 40%",
                    "Reduced operational costs by 30% through process optimization",
                    "Coordinated successful Series A fundraise ($15M)",
                ],
            ),
            Experience(
                company="GrowthCo",
                title="Business Operations Manager",
                location="San Francisco, CA",
                start_date=date(2017, 6, 1),
                end_date=date(2019, 12, 31),
                description="Managed operations and analytics for seed-stage startup.",
                achievements=[
                    "Built data infrastructure supporting growth from $1M to $10M ARR",
                    "Led cross-functional projects across eng, sales, and product teams",
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


def create_sample_criteria() -> SearchCriteria:
    """Create sample search criteria."""
    return SearchCriteria(
        titles=[
            "Chief of Staff",
            "Business Operations",
            "BizOps",
            "Head of Business Operations",
            "Director of Operations",
        ],
        locations=[
            "New York, NY",
            "San Francisco, CA",
            "Palo Alto, CA",
            "Remote",
        ],
        excluded_locations=["Israel"],
        company_sizes=[
            "1-10 employees",
            "11-50 employees",
            "51-200 employees",
        ],
        min_match_score=60,
        max_applications_per_day=25,
        required_keywords=[],  # Optional: add specific keywords
        excluded_keywords=["sales", "insurance"],  # Example exclusions
    )


def example_job_matching():
    """Demonstrate job matching functionality."""
    print("=" * 80)
    print("Job Matching Example")
    print("=" * 80)

    # Create profile and criteria
    profile = create_sample_profile()
    criteria = create_sample_criteria()

    # Initialize matcher (requires ANTHROPIC_API_KEY env var)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n⚠️  ANTHROPIC_API_KEY not set. Set it in .env file.")
        print("Example: ANTHROPIC_API_KEY=sk-ant-...")
        return

    matcher = JobMatcher(profile=profile, criteria=criteria, api_key=api_key)

    print(f"\n✓ Matcher initialized with {len(matcher.profile_keywords)} profile keywords")

    # Example jobs to test
    jobs = [
        Job(
            linkedin_job_id="job-001",
            title="Chief of Staff",
            company="Awesome Startup",
            location="New York, NY",
            description="""
            We're a Seed-stage startup (30 people) building the future of B2B SaaS.
            Seeking a Chief of Staff to work directly with our CEO.

            Responsibilities:
            - Lead strategic planning and OKR implementation
            - Coordinate cross-functional projects across engineering, sales, and product
            - Drive operational excellence and process improvements
            - Support fundraising and investor relations

            Requirements:
            - 5+ years in business operations or Chief of Staff roles
            - Experience at early-stage startups (Seed to Series A)
            - Strong analytical and project management skills
            - SQL and data analysis experience preferred
            - MBA or equivalent experience
            """,
            company_size="11-50 employees",
            experience_level="Mid-Senior level",
            easy_apply=True,
        ),
        Job(
            linkedin_job_id="job-002",
            title="Software Engineer",
            company="BigCorp Inc",
            location="Seattle, WA",
            description="""
            Senior Software Engineer role at large enterprise.

            Requirements:
            - 10+ years Java development
            - Distributed systems experience
            - Algorithm expertise
            """,
            company_size="5000-10000 employees",
            experience_level="Senior level",
            easy_apply=False,
        ),
        Job(
            linkedin_job_id="job-003",
            title="Director of Business Operations",
            company="Tech Ventures",
            location="Tel Aviv, Israel",
            description="""
            Leading business operations at a fast-growing Series A startup.
            Perfect for someone with Chief of Staff background.
            """,
            company_size="51-200 employees",
            easy_apply=True,
        ),
    ]

    # Test each job
    print("\n" + "=" * 80)
    print("Testing Jobs")
    print("=" * 80)

    for i, job in enumerate(jobs, 1):
        print(f"\n--- Job {i}: {job.title} at {job.company} ---")
        print(f"Location: {job.location}")
        print(f"Company Size: {job.company_size}")

        # Run matching pipeline
        updated_job, is_match = matcher.match_job(job)

        # Display results
        if updated_job.status.value == "rejected":
            if not matcher.keyword_filter(job):
                print("❌ FILTERED OUT (keyword/location/company size)")
            else:
                print(f"❌ NO MATCH - Score: {updated_job.match_score}/100")
        else:
            print(f"✅ MATCH! - Score: {updated_job.match_score}/100")
            print(f"\nReasoning: {updated_job.match_reasoning}")

            if updated_job.key_matches:
                print(f"\nKey Matches:")
                for match in updated_job.key_matches:
                    print(f"  ✓ {match}")

            if updated_job.concerns:
                print(f"\nConcerns:")
                for concern in updated_job.concerns:
                    print(f"  ⚠ {concern}")

    # Test custom question answering
    print("\n" + "=" * 80)
    print("Custom Question Answering")
    print("=" * 80)

    questions = [
        "Why are you interested in this Chief of Staff role?",
        "What experience do you have working with early-stage startups?",
        "Describe a time you led a cross-functional project.",
    ]

    for question in questions:
        print(f"\nQ: {question}")
        answer = matcher.answer_application_question(question)
        print(f"A: {answer}")

    print("\n" + "=" * 80)
    print("Example Complete!")
    print("=" * 80)


if __name__ == "__main__":
    example_job_matching()
