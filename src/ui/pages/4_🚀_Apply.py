"""Application Control and Tracking Page."""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime
import time
import uuid

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.models.application import Application, ApplicationStatus

st.set_page_config(page_title="Apply - Job Hunter", page_icon="🚀", layout="wide")

st.title("🚀 Application Control")
st.markdown("Control and track your job applications with rate limiting.")

# Initialize state
if "applications" not in st.session_state:
    st.session_state.applications = []
if "applications_today" not in st.session_state:
    st.session_state.applications_today = 0
if "application_queue" not in st.session_state:
    st.session_state.application_queue = []
if "is_applying" not in st.session_state:
    st.session_state.is_applying = False
if "selected_jobs" not in st.session_state:
    st.session_state.selected_jobs = set()
if "matched_jobs" not in st.session_state:
    st.session_state.matched_jobs = []

# Settings
DAILY_LIMIT = 25
DEFAULT_MIN_DELAY = 30
DEFAULT_MAX_DELAY = 90

# Rate limit dashboard
st.markdown("### 📊 Daily Progress")

progress_col1, progress_col2, progress_col3 = st.columns([2, 1, 1])

with progress_col1:
    progress = st.session_state.applications_today / DAILY_LIMIT
    st.progress(progress, text=f"Applications Today: {st.session_state.applications_today} / {DAILY_LIMIT}")

with progress_col2:
    remaining = DAILY_LIMIT - st.session_state.applications_today
    st.metric("Remaining", remaining)

with progress_col3:
    queue_size = len(st.session_state.application_queue)
    st.metric("In Queue", queue_size)

st.markdown("---")

# Queue management
st.markdown("### 📋 Application Queue")

# Get job details for queue
queue_jobs = []
for job_id in st.session_state.application_queue:
    for jm in st.session_state.matched_jobs:
        if jm.job.id == job_id:
            queue_jobs.append(jm)
            break

if not queue_jobs:
    st.info("No jobs in queue. Select jobs from the Results page to add them to the queue.")
    st.page_link("pages/3_📊_Results.py", label="Go to Results Page")
else:
    # Queue controls
    control_col1, control_col2, control_col3 = st.columns(3)

    with control_col1:
        dry_run = st.checkbox(
            "🔍 Dry Run Mode",
            value=True,
            help="Preview applications without actually submitting"
        )

    with control_col2:
        min_delay = st.number_input(
            "Min Delay (sec)",
            min_value=10,
            max_value=120,
            value=DEFAULT_MIN_DELAY,
            help="Minimum delay between applications"
        )

    with control_col3:
        max_delay = st.number_input(
            "Max Delay (sec)",
            min_value=30,
            max_value=300,
            value=DEFAULT_MAX_DELAY,
            help="Maximum delay between applications"
        )

    st.markdown("---")

    # Display queue
    for i, jm in enumerate(queue_jobs):
        job = jm.job
        with st.container():
            q_col1, q_col2, q_col3, q_col4 = st.columns([0.5, 4, 1, 1])

            with q_col1:
                st.markdown(f"**{i + 1}.**")

            with q_col2:
                st.markdown(f"**{job.title}** @ {job.company}")
                st.caption(f"{job.location} • Score: {jm.score}")

            with q_col3:
                if job.easy_apply:
                    st.markdown("⚡ Easy")
                else:
                    st.markdown("📝 Manual")

            with q_col4:
                if st.button("❌", key=f"remove_{job.id}", help="Remove from queue"):
                    st.session_state.application_queue.remove(job.id)
                    if job.id in st.session_state.selected_jobs:
                        st.session_state.selected_jobs.remove(job.id)
                    st.rerun()

    st.markdown("---")

    # Action buttons
    action_col1, action_col2, action_col3 = st.columns(3)

    with action_col1:
        start_disabled = st.session_state.is_applying or st.session_state.applications_today >= DAILY_LIMIT
        if st.button(
            "▶️ Start Applying",
            use_container_width=True,
            type="primary",
            disabled=start_disabled
        ):
            st.session_state.is_applying = True
            st.rerun()

    with action_col2:
        if st.button(
            "⏸️ Pause",
            use_container_width=True,
            disabled=not st.session_state.is_applying
        ):
            st.session_state.is_applying = False
            st.rerun()

    with action_col3:
        if st.button("🗑️ Clear Queue", use_container_width=True):
            st.session_state.application_queue = []
            st.session_state.selected_jobs.clear()
            st.rerun()

    # Application simulation
    if st.session_state.is_applying and queue_jobs:
        st.markdown("---")
        st.markdown("### 🔄 Applying...")

        status_container = st.empty()
        progress_bar = st.progress(0)
        log_container = st.empty()

        logs = []
        total_jobs = len(queue_jobs)

        for i, jm in enumerate(queue_jobs):
            if not st.session_state.is_applying:
                break

            if st.session_state.applications_today >= DAILY_LIMIT:
                logs.append(f"⚠️ Daily limit reached ({DAILY_LIMIT})")
                break

            job = jm.job
            progress_bar.progress((i + 1) / total_jobs)

            with status_container.container():
                st.markdown(f"**Currently applying to:** {job.title} @ {job.company}")
                if dry_run:
                    st.caption("🔍 Dry run mode - not actually submitting")

            # Simulate application
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 📝 Starting: {job.title} @ {job.company}")
            log_container.text("\n".join(logs[-5:]))
            time.sleep(1)

            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 {'Simulating' if dry_run else 'Filling'} application form...")
            log_container.text("\n".join(logs[-5:]))
            time.sleep(1)

            # Create application record
            app = Application(
                id=str(uuid.uuid4()),
                job_id=job.id,
                job_title=job.title,
                company=job.company,
                status=ApplicationStatus.SUBMITTED if not dry_run else ApplicationStatus.SKIPPED,
                match_score=jm.score,
                notes="Dry run - not submitted" if dry_run else ""
            )

            if not dry_run:
                app.mark_submitted()
                st.session_state.applications_today += 1
            else:
                app.mark_skipped("Dry run mode")

            st.session_state.applications.append(app)

            # Remove from queue
            if job.id in st.session_state.application_queue:
                st.session_state.application_queue.remove(job.id)
            if job.id in st.session_state.selected_jobs:
                st.session_state.selected_jobs.remove(job.id)

            status_emoji = "✅" if not dry_run else "🔍"
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {status_emoji} {'Submitted' if not dry_run else 'Simulated'}: {job.title}")
            log_container.text("\n".join(logs[-5:]))

            # Delay before next
            if i < total_jobs - 1 and st.session_state.is_applying:
                import random
                delay = random.randint(min_delay, max_delay)
                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ Waiting {delay}s before next application...")
                log_container.text("\n".join(logs[-5:]))

                # Show countdown
                for remaining in range(delay, 0, -1):
                    if not st.session_state.is_applying:
                        break
                    status_container.markdown(f"**Waiting:** {remaining}s until next application")
                    time.sleep(1)

        st.session_state.is_applying = False
        status_container.success("✅ Batch complete!")
        st.rerun()

st.markdown("---")

# Application history
st.markdown("### 📜 Application History")

if not st.session_state.applications:
    st.info("No applications yet. Start applying to build your history.")
else:
    # Filter options
    hist_col1, hist_col2 = st.columns([3, 1])

    with hist_col1:
        status_filter = st.multiselect(
            "Filter by Status",
            options=[s.value for s in ApplicationStatus],
            default=[],
            label_visibility="collapsed"
        )

    with hist_col2:
        if st.button("📥 Export CSV", use_container_width=True):
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Date", "Job Title", "Company", "Score", "Status", "Notes"])

            for app in st.session_state.applications:
                writer.writerow([
                    app.created_at.strftime("%Y-%m-%d %H:%M"),
                    app.job_title,
                    app.company,
                    app.match_score,
                    app.status.value,
                    app.notes
                ])

            st.download_button(
                "Download",
                output.getvalue(),
                "applications.csv",
                "text/csv"
            )

    # Display applications
    filtered_apps = st.session_state.applications
    if status_filter:
        filtered_apps = [a for a in filtered_apps if a.status.value in status_filter]

    # Sort by date (newest first)
    filtered_apps = sorted(filtered_apps, key=lambda x: x.created_at, reverse=True)

    for app in filtered_apps:
        with st.container():
            app_col1, app_col2, app_col3, app_col4 = st.columns([3, 1, 1, 1])

            with app_col1:
                st.markdown(f"**{app.job_title}** @ {app.company}")
                st.caption(app.created_at.strftime("%Y-%m-%d %H:%M"))

            with app_col2:
                st.markdown(f"Score: **{app.match_score}**")

            with app_col3:
                status_emoji = {
                    ApplicationStatus.SUBMITTED: "✅",
                    ApplicationStatus.SKIPPED: "⏭️",
                    ApplicationStatus.FAILED: "❌",
                    ApplicationStatus.VIEWED: "👁️",
                    ApplicationStatus.REJECTED: "🚫",
                    ApplicationStatus.INTERVIEW: "🎉",
                    ApplicationStatus.QUEUED: "⏳",
                    ApplicationStatus.IN_PROGRESS: "🔄"
                }
                st.markdown(f"{status_emoji.get(app.status, '❓')} {app.status.value}")

            with app_col4:
                if app.notes:
                    st.caption(app.notes[:20] + "..." if len(app.notes) > 20 else app.notes)

        st.markdown("---")

# Tips
st.markdown("---")
with st.expander("💡 Tips for Safe Automation"):
    st.markdown("""
    - **Rate Limiting**: The tool enforces a maximum of 25 applications per day
    - **Random Delays**: Delays between 30-90 seconds help avoid detection
    - **Dry Run Mode**: Always test with dry run first before actual applications
    - **Easy Apply Only**: Focus on Easy Apply jobs for smoother automation
    - **Monitor Progress**: Watch for any errors or unusual behavior
    - **Take Breaks**: Don't run the tool continuously for hours
    - **Update Regularly**: Keep your profile and search criteria up to date
    """)
