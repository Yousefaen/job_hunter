"""Job Hunter - Main Streamlit Application."""

import streamlit as st
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

st.set_page_config(
    page_title="Job Hunter",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "profile" not in st.session_state:
    st.session_state.profile = None
if "search_criteria" not in st.session_state:
    from src.models.search_criteria import SearchCriteria
    st.session_state.search_criteria = SearchCriteria()
if "matched_jobs" not in st.session_state:
    st.session_state.matched_jobs = []
if "selected_jobs" not in st.session_state:
    st.session_state.selected_jobs = set()
if "applications" not in st.session_state:
    st.session_state.applications = []
if "applications_today" not in st.session_state:
    st.session_state.applications_today = 0

# Sidebar
st.sidebar.title("🎯 Job Hunter")
st.sidebar.markdown("---")

# Profile status
if st.session_state.profile:
    st.sidebar.success(f"✅ {st.session_state.profile.contact.name}")
    if st.session_state.profile.get_current_title():
        st.sidebar.caption(st.session_state.profile.get_current_title())
else:
    st.sidebar.warning("⚠️ No resume uploaded")

st.sidebar.markdown("---")

# Daily limit indicator
daily_limit = 25
progress = st.session_state.applications_today / daily_limit
st.sidebar.markdown("**Daily Applications**")
st.sidebar.progress(progress, text=f"{st.session_state.applications_today} / {daily_limit}")

st.sidebar.markdown("---")

# Quick stats
st.sidebar.markdown("**Quick Stats**")
col1, col2 = st.sidebar.columns(2)
col1.metric("Jobs Found", len(st.session_state.matched_jobs))
col2.metric("Selected", len(st.session_state.selected_jobs))

st.sidebar.markdown("---")
st.sidebar.markdown(
    "Made with Streamlit | "
    "[GitHub](https://github.com/Yousefaen/job_hunter)"
)

# Main content
st.title("🎯 Job Hunter")
st.markdown("### Intelligent LinkedIn Job Application Assistant")

st.markdown("---")

# Welcome message and navigation
st.markdown("""
Welcome to Job Hunter! This tool helps you find and apply to jobs on LinkedIn with AI-powered matching.

**Get Started:**

1. **📄 Resume** - Upload your resume (PDF or JSON)
2. **🔍 Search** - Configure your job search criteria
3. **📊 Results** - View matched jobs with AI justifications
4. **🚀 Apply** - Control and track your applications

Use the sidebar to navigate between pages.
""")

# Quick action cards
st.markdown("---")
st.markdown("### Quick Actions")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("#### 📄 Resume")
    if st.session_state.profile:
        st.success("Uploaded")
        st.caption(f"{len(st.session_state.profile.skills)} skills")
    else:
        st.warning("Not uploaded")
    st.page_link("pages/1_📄_Resume.py", label="Go to Resume", use_container_width=True)

with col2:
    st.markdown("#### 🔍 Search")
    criteria = st.session_state.search_criteria
    st.info(f"{len(criteria.titles)} titles")
    st.caption(f"{len(criteria.locations)} locations")
    st.page_link("pages/2_🔍_Search.py", label="Configure Search", use_container_width=True)

with col3:
    st.markdown("#### 📊 Results")
    if st.session_state.matched_jobs:
        above_threshold = len([
            j for j in st.session_state.matched_jobs
            if j.score >= criteria.min_match_score
        ])
        st.success(f"{above_threshold} matches")
    else:
        st.info("No results yet")
    st.page_link("pages/3_📊_Results.py", label="View Results", use_container_width=True)

with col4:
    st.markdown("#### 🚀 Apply")
    if st.session_state.selected_jobs:
        st.success(f"{len(st.session_state.selected_jobs)} queued")
    else:
        st.info("No jobs queued")
    st.page_link("pages/4_🚀_Apply.py", label="Start Applying", use_container_width=True)

# Footer
st.markdown("---")
st.caption(
    "⚠️ **Disclaimer**: This tool automates LinkedIn interactions. "
    "Use responsibly and respect rate limits. "
    "The tool is for personal use only."
)
