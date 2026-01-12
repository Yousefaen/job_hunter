"""Job Results and Matching Page."""

import streamlit as st
from pathlib import Path
import sys
import uuid
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.models.job import Job, JobMatch, JobStatus
from src.models.search_criteria import SearchCriteria

st.set_page_config(page_title="Results - Job Hunter", page_icon="📊", layout="wide")

st.title("📊 Job Results")
st.markdown("View matched jobs with AI-powered scoring and justifications.")

# Initialize state
if "matched_jobs" not in st.session_state:
    st.session_state.matched_jobs = []
if "selected_jobs" not in st.session_state:
    st.session_state.selected_jobs = set()
if "search_criteria" not in st.session_state:
    st.session_state.search_criteria = SearchCriteria()

criteria = st.session_state.search_criteria


def get_score_color(score: int) -> str:
    """Get color for score display."""
    if score >= 80:
        return "🟢"
    elif score >= 60:
        return "🟡"
    else:
        return "🔴"


def get_job_matcher():
    """Get JobMatcher instance if API key is available."""
    profile = st.session_state.get("profile")
    api_key = os.getenv("ANTHROPIC_API_KEY") or st.session_state.get("anthropic_api_key")

    if not profile:
        return None, "No profile uploaded. Go to Resume page first."
    if not api_key:
        return None, "No API key. Set ANTHROPIC_API_KEY or enter in sidebar."

    try:
        from src.agent.job_matcher import JobMatcher
        matcher = JobMatcher(profile=profile, criteria=criteria, api_key=api_key)
        return matcher, None
    except Exception as e:
        return None, str(e)


def match_job_with_ai(job: Job) -> JobMatch:
    """Match a job using AI if available, otherwise use simple matching."""
    profile = st.session_state.get("profile")
    matcher, error = get_job_matcher()

    if matcher:
        try:
            result = matcher.score_job_match(job)
            return JobMatch(
                job=job,
                score=result.score,
                justification=result.reasoning,
                matched_skills=result.key_matches,
                concerns=result.concerns,
            )
        except Exception as e:
            st.warning(f"AI matching failed: {e}. Using basic matching.")

    # Fallback to basic matching
    return basic_match(job, profile)


def basic_match(job: Job, profile) -> JobMatch:
    """Basic keyword matching without AI."""
    if not profile:
        return JobMatch(job=job, score=50, justification="No profile for matching")

    score = 50
    matched = []
    concerns = []

    job_text = f"{job.title} {job.description}".lower()

    # Check skills
    for skill in profile.skills[:10]:
        if skill.lower() in job_text:
            score += 5
            matched.append(f"Skill: {skill}")

    # Check title alignment
    title_keywords = ["chief", "staff", "operations", "bizops", "director"]
    for kw in title_keywords:
        if kw in job.title.lower():
            score += 10
            matched.append(f"Title match: {kw}")
            break

    # Check company size
    if job.company_size:
        size_text = job.company_size.lower()
        if any(s in size_text for s in ["1-10", "11-50", "51-200"]):
            score += 10
            matched.append("Startup size company")
        elif "500" in size_text or "1000" in size_text:
            concerns.append("Large company - may not be startup")

    score = min(100, score)

    justification = f"Basic matching found {len(matched)} alignment points. "
    if score >= 70:
        justification += "Good potential fit based on keywords."
    elif score >= 50:
        justification += "Moderate fit - review job details."
    else:
        justification += "Limited keyword matches."

    return JobMatch(
        job=job,
        score=score,
        justification=justification,
        matched_skills=matched,
        concerns=concerns,
    )


# Sidebar: API Key configuration
with st.sidebar:
    st.markdown("### 🔑 AI Matching")

    has_env_key = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_session_key = bool(st.session_state.get("anthropic_api_key"))

    if has_env_key:
        st.success("✅ API key from environment")
    elif has_session_key:
        st.success("✅ API key configured")
    else:
        st.warning("⚠️ No API key - using basic matching")
        api_key_input = st.text_input(
            "Anthropic API Key",
            type="password",
            help="Enter your Anthropic API key for AI-powered matching"
        )
        if api_key_input:
            st.session_state.anthropic_api_key = api_key_input
            st.rerun()


# Toolbar
col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

with col1:
    sort_by = st.selectbox(
        "Sort by",
        ["Match Score (High to Low)", "Match Score (Low to High)", "Company Name"],
        label_visibility="collapsed"
    )

with col2:
    filter_score = st.selectbox(
        "Filter by Score",
        ["All Scores", "Excellent (80+)", "Good (60+)", "Below Threshold"],
        label_visibility="collapsed"
    )

with col3:
    filter_location = st.selectbox(
        "Filter by Location",
        ["All Locations", "Remote Only", "On-site Only"],
        label_visibility="collapsed"
    )

with col4:
    if st.button("🔄 Re-score All", use_container_width=True):
        if st.session_state.matched_jobs:
            with st.spinner("Re-scoring jobs with AI..."):
                new_matches = []
                for jm in st.session_state.matched_jobs:
                    new_match = match_job_with_ai(jm.job)
                    new_matches.append(new_match)
                st.session_state.matched_jobs = new_matches
            st.success("✅ Re-scored all jobs!")
            st.rerun()

st.markdown("---")

# Add job manually
with st.expander("➕ Add Job Manually", expanded=not st.session_state.matched_jobs):
    st.markdown("Paste a job posting to analyze and score it.")

    add_col1, add_col2 = st.columns(2)

    with add_col1:
        job_title = st.text_input("Job Title", placeholder="Chief of Staff")
        job_company = st.text_input("Company", placeholder="TechStartup Inc.")
        job_location = st.text_input("Location", placeholder="New York, NY or Remote")

    with add_col2:
        job_company_size = st.text_input("Company Size", placeholder="50 employees")
        job_url = st.text_input("LinkedIn URL (optional)", placeholder="https://linkedin.com/jobs/view/...")
        job_easy_apply = st.checkbox("Easy Apply Available", value=True)

    job_description = st.text_area(
        "Job Description",
        height=200,
        placeholder="Paste the full job description here..."
    )

    if st.button("🎯 Analyze & Score Job", use_container_width=True, type="primary"):
        if job_title and job_company and job_description:
            job = Job(
                linkedin_job_id=str(uuid.uuid4())[:8],
                title=job_title,
                company=job_company,
                location=job_location or "Not specified",
                description=job_description,
                company_size=job_company_size,
                easy_apply=job_easy_apply,
                application_url=job_url if job_url else None,
            )

            with st.spinner("Analyzing job with AI..."):
                job_match = match_job_with_ai(job)

            st.session_state.matched_jobs.append(job_match)
            st.success(f"✅ Added job: {job_title} (Score: {job_match.score})")
            st.rerun()
        else:
            st.error("Please fill in Title, Company, and Description")

# Sample jobs section
with st.expander("📥 Load Sample Jobs"):
    st.markdown("Load sample jobs to test the interface.")

    sample_jobs = [
        {
            "title": "Chief of Staff",
            "company": "TechStartup Inc.",
            "location": "New York, NY",
            "company_size": "25 employees",
            "description": "We're looking for a Chief of Staff to work directly with the CEO. You'll drive strategic initiatives, manage cross-functional projects, and help scale our Series A startup. Requires 3+ years of operations experience, strong analytical skills, and MBA preferred.",
            "easy_apply": True,
        },
        {
            "title": "Head of Business Operations",
            "company": "AI Health Co.",
            "location": "Remote",
            "company_size": "85 employees",
            "description": "Join our growing healthcare AI company as Head of Business Operations. Lead operational excellence, build scalable processes, and drive growth initiatives. Looking for someone with startup experience, data-driven mindset, and leadership skills.",
            "easy_apply": True,
        },
        {
            "title": "Director of Operations",
            "company": "FinanceAI",
            "location": "San Francisco, CA",
            "company_size": "45 employees",
            "description": "Director of Operations needed for our fintech startup. You'll oversee daily operations, manage vendor relationships, and implement operational strategies. 5+ years experience required. Strong background in finance preferred.",
            "easy_apply": True,
        },
    ]

    if st.button("📥 Load & Score Sample Jobs", use_container_width=True):
        with st.spinner("Loading and scoring sample jobs..."):
            for sample in sample_jobs:
                job = Job(
                    linkedin_job_id=str(uuid.uuid4())[:8],
                    title=sample["title"],
                    company=sample["company"],
                    location=sample["location"],
                    company_size=sample["company_size"],
                    description=sample["description"],
                    easy_apply=sample["easy_apply"],
                )
                job_match = match_job_with_ai(job)
                st.session_state.matched_jobs.append(job_match)

        st.success(f"✅ Loaded {len(sample_jobs)} jobs!")
        st.rerun()

# Stats bar
if st.session_state.matched_jobs:
    total = len(st.session_state.matched_jobs)
    above_threshold = len([j for j in st.session_state.matched_jobs if j.score >= criteria.min_match_score])
    easy_apply_count = len([j for j in st.session_state.matched_jobs if j.job.easy_apply])

    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    stat_col1.metric("Total Jobs", total)
    stat_col2.metric("Above Threshold", above_threshold)
    stat_col3.metric("Easy Apply", easy_apply_count)
    stat_col4.metric("Selected", len(st.session_state.selected_jobs))

    st.markdown("---")

# Job list
if not st.session_state.matched_jobs:
    st.info("No jobs yet. Add a job manually above or load sample jobs to get started.")
else:
    # Apply filters
    filtered_jobs = st.session_state.matched_jobs.copy()

    # Score filter
    if filter_score == "Excellent (80+)":
        filtered_jobs = [j for j in filtered_jobs if j.score >= 80]
    elif filter_score == "Good (60+)":
        filtered_jobs = [j for j in filtered_jobs if j.score >= 60]
    elif filter_score == "Below Threshold":
        filtered_jobs = [j for j in filtered_jobs if j.score < criteria.min_match_score]

    # Location filter
    if filter_location == "Remote Only":
        filtered_jobs = [j for j in filtered_jobs if j.job.is_remote()]
    elif filter_location == "On-site Only":
        filtered_jobs = [j for j in filtered_jobs if not j.job.is_remote()]

    # Sort
    if sort_by == "Match Score (High to Low)":
        filtered_jobs.sort(key=lambda x: x.score, reverse=True)
    elif sort_by == "Match Score (Low to High)":
        filtered_jobs.sort(key=lambda x: x.score)
    elif sort_by == "Company Name":
        filtered_jobs.sort(key=lambda x: x.job.company)

    # Bulk actions
    action_col1, action_col2, action_col3, action_col4 = st.columns([1, 1, 1, 1])
    with action_col1:
        if st.button("☑️ Select Above Threshold"):
            for jm in filtered_jobs:
                if jm.score >= criteria.min_match_score:
                    st.session_state.selected_jobs.add(jm.job.linkedin_job_id)
            st.rerun()
    with action_col2:
        if st.button("☐ Deselect All"):
            st.session_state.selected_jobs.clear()
            st.rerun()
    with action_col3:
        if st.button("🗑️ Clear All Jobs"):
            st.session_state.matched_jobs = []
            st.session_state.selected_jobs.clear()
            st.rerun()

    st.markdown("---")

    # Display jobs
    for job_match in filtered_jobs:
        job = job_match.job
        score = job_match.score
        job_id = job.linkedin_job_id
        is_selected = job_id in st.session_state.selected_jobs

        # Job card
        with st.container():
            header_col1, header_col2, header_col3 = st.columns([0.5, 6, 1.5])

            with header_col1:
                selected = st.checkbox(
                    "Select",
                    value=is_selected,
                    key=f"select_{job_id}",
                    label_visibility="collapsed"
                )
                if selected and job_id not in st.session_state.selected_jobs:
                    st.session_state.selected_jobs.add(job_id)
                elif not selected and job_id in st.session_state.selected_jobs:
                    st.session_state.selected_jobs.remove(job_id)

            with header_col2:
                st.markdown(f"### {job.title}")
                meta_parts = [f"**{job.company}**", job.location]
                if job.company_size:
                    meta_parts.append(job.company_size)
                st.markdown(" • ".join(meta_parts))

                badges = []
                if job.easy_apply:
                    badges.append("⚡ Easy Apply")
                if job.is_remote():
                    badges.append("🌐 Remote")
                if badges:
                    st.markdown(" | ".join(badges))

            with header_col3:
                color = get_score_color(score)
                st.markdown(f"### {color} {score}")
                st.caption("Match Score")

            # Expandable justification
            with st.expander("📋 View Match Details"):
                st.markdown("**AI Justification:**")
                st.markdown(job_match.justification)

                if job_match.matched_skills:
                    st.markdown("**✅ Matching Points:**")
                    for skill in job_match.matched_skills:
                        st.markdown(f"• {skill}")

                if job_match.concerns:
                    st.markdown("**⚠️ Considerations:**")
                    for concern in job_match.concerns:
                        st.markdown(f"• {concern}")

                st.markdown("**Job Description:**")
                desc = job.description or ""
                st.markdown(desc[:500] + "..." if len(desc) > 500 else desc)

                if job.application_url:
                    st.markdown(f"[🔗 View on LinkedIn]({job.application_url})")

            st.markdown("---")

    # Bottom action bar
    if st.session_state.selected_jobs:
        st.markdown("### Ready to Apply?")
        apply_col1, apply_col2 = st.columns(2)

        with apply_col1:
            if st.button(
                f"🚀 Apply to Selected ({len(st.session_state.selected_jobs)})",
                use_container_width=True,
                type="primary"
            ):
                st.session_state.application_queue = list(st.session_state.selected_jobs)
                st.switch_page("pages/4_🚀_Apply.py")

        with apply_col2:
            above_threshold_ids = [
                jm.job.linkedin_job_id for jm in st.session_state.matched_jobs
                if jm.score >= criteria.min_match_score and jm.job.easy_apply
            ]
            if st.button(
                f"🚀 Apply to All Easy Apply ({len(above_threshold_ids)})",
                use_container_width=True
            ):
                st.session_state.selected_jobs = set(above_threshold_ids)
                st.session_state.application_queue = above_threshold_ids
                st.switch_page("pages/4_🚀_Apply.py")
