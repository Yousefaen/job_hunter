"""Job Results and Matching Page."""

import streamlit as st
from pathlib import Path
import sys
import uuid
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.models.job import Job, JobMatch
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


def generate_mock_justification(job: Job, profile) -> tuple[str, list, list]:
    """Generate a mock justification for demo purposes."""
    if not profile:
        return "No profile uploaded for matching.", [], []

    matched = []
    concerns = []

    # Check title match
    title_lower = job.title.lower()
    for exp in profile.work_experience:
        if any(word in exp.title.lower() for word in ["chief", "staff", "operations", "director"]):
            matched.append(f"Your '{exp.title}' experience aligns with this role")
            break

    # Check skills
    job_desc_lower = job.description.lower()
    for skill in profile.skills[:5]:
        if skill.lower() in job_desc_lower:
            matched.append(f"Skill match: {skill}")

    if not matched:
        matched.append("General operations/leadership background")

    # Add concerns based on job
    if "5+ years" in job.description or "7+ years" in job.description:
        concerns.append("May require more years of experience than shown")
    if job.company_size and "201" in job.company_size:
        concerns.append("Company may be larger than target (Seed-Series A)")

    justification = f"Based on your profile, this {job.title} role at {job.company} "
    if len(matched) > 1:
        justification += f"shows {len(matched)} key alignments with your background. "
    else:
        justification += "shows potential alignment with your background. "

    if job.location.lower() == "remote" or "remote" in job.location.lower():
        justification += "The remote option provides flexibility. "

    return justification, matched, concerns


# Toolbar
col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

with col1:
    sort_by = st.selectbox(
        "Sort by",
        ["Match Score (High to Low)", "Match Score (Low to High)", "Company Name", "Date Posted"],
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
    if st.button("🔄 Refresh Scores", use_container_width=True):
        st.info("Re-scoring jobs with AI... (demo)")

st.markdown("---")

# Add sample jobs section (for demo)
with st.expander("➕ Add Sample Jobs (Demo Mode)", expanded=not st.session_state.matched_jobs):
    st.markdown("Add sample jobs to test the interface. In production, jobs come from LinkedIn search.")

    sample_jobs = [
        {
            "title": "Chief of Staff",
            "company": "TechStartup Inc.",
            "location": "New York, NY",
            "company_size": "25 employees",
            "description": "We're looking for a Chief of Staff to work directly with the CEO. You'll drive strategic initiatives, manage cross-functional projects, and help scale our Series A startup. Requires 3+ years of operations experience, strong analytical skills, and MBA preferred.",
            "easy_apply": True,
            "score": 92
        },
        {
            "title": "Head of Business Operations",
            "company": "AI Health Co.",
            "location": "Remote",
            "company_size": "85 employees",
            "description": "Join our growing healthcare AI company as Head of Business Operations. Lead operational excellence, build scalable processes, and drive growth initiatives. Looking for someone with startup experience, data-driven mindset, and leadership skills.",
            "easy_apply": True,
            "score": 85
        },
        {
            "title": "Director of Operations",
            "company": "FinanceAI",
            "location": "San Francisco, CA",
            "company_size": "45 employees",
            "description": "Director of Operations needed for our fintech startup. You'll oversee daily operations, manage vendor relationships, and implement operational strategies. 5+ years experience required. Strong background in finance preferred.",
            "easy_apply": True,
            "score": 78
        },
        {
            "title": "BizOps Lead",
            "company": "CloudScale",
            "location": "Remote",
            "company_size": "120 employees",
            "description": "BizOps Lead to drive business operations and analytics. Work with leadership on strategic planning, KPI tracking, and process improvement. Series B startup looking for analytical, data-driven operators.",
            "easy_apply": False,
            "score": 72
        },
        {
            "title": "Operations Manager",
            "company": "RetailTech",
            "location": "Austin, TX",
            "company_size": "200 employees",
            "description": "Operations Manager for retail technology company. Manage supply chain, logistics, and operational efficiency. Looking for someone with retail or e-commerce experience.",
            "easy_apply": True,
            "score": 55
        }
    ]

    if st.button("📥 Load Sample Jobs", use_container_width=True):
        profile = st.session_state.get("profile")

        for sample in sample_jobs:
            job = Job(
                id=str(uuid.uuid4()),
                title=sample["title"],
                company=sample["company"],
                location=sample["location"],
                company_size=sample["company_size"],
                description=sample["description"],
                easy_apply=sample["easy_apply"],
                remote="remote" in sample["location"].lower(),
                posted_date="2 days ago",
                url=f"https://linkedin.com/jobs/view/{uuid.uuid4().hex[:8]}"
            )

            justification, matched, concerns = generate_mock_justification(job, profile)

            job_match = JobMatch(
                job=job,
                score=sample["score"],
                justification=justification,
                matched_skills=matched,
                concerns=concerns
            )

            # Check if already exists
            existing_ids = [m.job.id for m in st.session_state.matched_jobs]
            if job.id not in existing_ids:
                st.session_state.matched_jobs.append(job_match)

        st.success(f"✅ Loaded {len(sample_jobs)} sample jobs!")
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
    st.info("No jobs loaded yet. Add sample jobs above or run a search from the Search page.")
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
    action_col1, action_col2, action_col3 = st.columns([1, 1, 2])
    with action_col1:
        if st.button("☑️ Select All Above Threshold"):
            for jm in filtered_jobs:
                if jm.score >= criteria.min_match_score:
                    st.session_state.selected_jobs.add(jm.job.id)
            st.rerun()
    with action_col2:
        if st.button("☐ Deselect All"):
            st.session_state.selected_jobs.clear()
            st.rerun()

    st.markdown("---")

    # Display jobs
    for job_match in filtered_jobs:
        job = job_match.job
        score = job_match.score
        is_selected = job.id in st.session_state.selected_jobs

        # Job card
        with st.container():
            header_col1, header_col2, header_col3 = st.columns([0.5, 6, 1.5])

            with header_col1:
                # Checkbox for selection
                selected = st.checkbox(
                    "Select",
                    value=is_selected,
                    key=f"select_{job.id}",
                    label_visibility="collapsed"
                )
                if selected and job.id not in st.session_state.selected_jobs:
                    st.session_state.selected_jobs.add(job.id)
                elif not selected and job.id in st.session_state.selected_jobs:
                    st.session_state.selected_jobs.remove(job.id)

            with header_col2:
                st.markdown(f"### {job.title}")
                meta_parts = [f"**{job.company}**", job.location]
                if job.company_size:
                    meta_parts.append(job.company_size)
                if job.posted_date:
                    meta_parts.append(f"Posted {job.posted_date}")
                st.markdown(" • ".join(meta_parts))

                # Badges
                badges = []
                if job.easy_apply:
                    badges.append("⚡ Easy Apply")
                if job.is_remote():
                    badges.append("🌐 Remote")
                if badges:
                    st.markdown(" | ".join(badges))

            with header_col3:
                # Score display
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
                st.markdown(job.description[:500] + "..." if len(job.description) > 500 else job.description)

                if job.url:
                    st.markdown(f"[🔗 View on LinkedIn]({job.url})")

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
                jm.job.id for jm in st.session_state.matched_jobs
                if jm.score >= criteria.min_match_score and jm.job.easy_apply
            ]
            if st.button(
                f"🚀 Apply to All Easy Apply ({len(above_threshold_ids)})",
                use_container_width=True
            ):
                st.session_state.selected_jobs = set(above_threshold_ids)
                st.session_state.application_queue = above_threshold_ids
                st.switch_page("pages/4_🚀_Apply.py")
