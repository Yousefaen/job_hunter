# Job Hunter UI Layer - Implementation Plan

## Executive Summary

This plan outlines adding a web-based UI layer to the existing job_hunter CLI application. The UI will provide a user-friendly interface for resume management, job search configuration, viewing matched results with justifications, and controlling the Easy Apply automation.

---

## Technology Recommendation

### Option A: Streamlit (Recommended for MVP)

| Aspect | Details |
|--------|---------|
| **Framework** | Streamlit 1.30+ |
| **Pros** | Rapid development, Python-native, built-in components, easy deployment |
| **Cons** | Limited customization, not ideal for complex interactions |
| **Best For** | Quick MVP, single-user tool, data-focused interfaces |

### Option B: FastAPI + React (Recommended for Production)

| Aspect | Details |
|--------|---------|
| **Backend** | FastAPI 0.109+ with async support |
| **Frontend** | React 18+ with TypeScript, Tailwind CSS |
| **Pros** | Full control, scalable, professional UX, real-time updates via WebSocket |
| **Cons** | More development effort, separate frontend/backend |
| **Best For** | Production-ready application, multi-user, advanced features |

### Recommendation

**Start with Streamlit** for a functional MVP that can be built quickly, then optionally migrate to FastAPI + React for a more polished production version.

---

## Proposed Architecture

### Directory Structure

```
job_hunter/
├── src/
│   ├── ... (existing modules)
│   └── ui/                         # NEW: UI layer
│       ├── __init__.py
│       ├── app.py                  # Streamlit main app
│       ├── pages/
│       │   ├── __init__.py
│       │   ├── 1_resume.py         # Resume upload & preview
│       │   ├── 2_search.py         # Search criteria configuration
│       │   ├── 3_results.py        # Job matches & justifications
│       │   └── 4_applications.py   # Application tracking & control
│       ├── components/
│       │   ├── __init__.py
│       │   ├── resume_uploader.py  # Resume upload component
│       │   ├── job_card.py         # Job listing card component
│       │   ├── match_score.py      # Match score visualization
│       │   └── rate_limit_bar.py   # Rate limit status display
│       ├── services/
│       │   ├── __init__.py
│       │   ├── session_state.py    # Streamlit session management
│       │   ├── job_service.py      # Job search/match orchestration
│       │   └── apply_service.py    # Application submission service
│       └── utils/
│           ├── __init__.py
│           └── formatting.py       # Display helpers
├── static/                         # NEW: Static assets
│   ├── css/
│   └── images/
└── config/
    └── ui_settings.yaml            # NEW: UI-specific config
```

---

## Core UI Features

### 1. Resume Management Page

**Purpose**: Upload and manage user's resume

**Features**:
- Drag-and-drop PDF upload
- JSON profile creation/editing form
- Parsed resume preview with structured sections:
  - Contact information
  - Skills (with keyword extraction display)
  - Work experience timeline
  - Education
- Resume validation status indicators
- Option to save/update profile
- View extracted keywords for job matching

**Technical Integration**:
- Uses existing `src/resume/parser.py` for PDF/JSON parsing
- Uses `src/resume/profile.py` `UserProfile` model
- Stores uploaded resumes in `data/resumes/`

**UI Components**:
```python
# Resume upload widget
uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "json"])

# Profile preview
st.json(profile.model_dump())

# Skills tag display
st.multiselect("Extracted Skills", profile.skills, profile.skills)
```

---

### 2. Search Criteria Configuration Page

**Purpose**: Configure job search parameters

**Features**:
- **Job Titles**: Multi-select with custom input
  - Default: Chief of Staff, BizOps, Head of Business Operations, Director of Operations
- **Locations**: Multi-select with custom input
  - City/Country selection
  - Remote toggle
  - Default: New York, Palo Alto/Bay Area, Remote
- **Filters**:
  - Experience level (Entry, Mid, Senior, Director)
  - Company size (1-10, 11-50, 51-200 employees)
  - Date posted (24h, Week, Month)
  - Easy Apply only toggle
- **Exclusions**:
  - Excluded locations (e.g., Israel)
  - Excluded companies (blocklist)
  - Excluded keywords
- **Match Threshold**: Slider for minimum match score (0-100)
- Save/Load search presets

**Technical Integration**:
- Creates/updates `src/models/search_criteria.py` model
- Persists to `config/search_criteria.yaml`
- Triggers new searches via `src/agent/job_searcher.py`

**UI Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 Job Search Criteria                                      │
├─────────────────────────────────────────────────────────────┤
│ Job Titles                          │ Locations             │
│ [Chief of Staff        ] [+]        │ [New York, NY    ] [+]│
│ [Business Operations   ] [x]        │ [Remote          ] [x]│
│ [Director of Operations] [x]        │ [Palo Alto, CA   ] [x]│
├─────────────────────────────────────────────────────────────┤
│ Experience Level        │ Company Size       │ Posted       │
│ ○ Entry                 │ ☑ 1-10 employees   │ ○ 24 hours   │
│ ● Mid-Senior            │ ☑ 11-50 employees  │ ● Past week  │
│ ● Senior                │ ☑ 51-200 employees │ ○ Past month │
├─────────────────────────────────────────────────────────────┤
│ Match Threshold: [====●=====] 60%                           │
│ ☑ Easy Apply Only                                           │
├─────────────────────────────────────────────────────────────┤
│ Excluded: Israel                                            │
├─────────────────────────────────────────────────────────────┤
│             [ Save Preset ]  [ 🔍 Search Jobs ]             │
└─────────────────────────────────────────────────────────────┘
```

---

### 3. Job Results & Matching Page

**Purpose**: View matched jobs with AI-generated justifications

**Features**:
- **Job Cards Display**: Scrollable list of matched jobs
  - Company name & logo (if available)
  - Job title
  - Location (with remote badge)
  - Company size indicator
  - Match score (0-100) with color coding:
    - 80-100: Green (Excellent match)
    - 60-79: Yellow (Good match)
    - Below 60: Red (Poor match)
  - Posted date
  - Easy Apply badge
- **Match Justification Panel**: Expandable section per job
  - AI-generated explanation of why the job matches
  - Key matching skills highlighted
  - Potential concerns/gaps noted
  - Company stage assessment
- **Filtering & Sorting**:
  - Sort by: Match score, Date posted, Company name
  - Filter by: Score range, Location, Company size
- **Bulk Actions**:
  - Select all / Deselect all
  - Checkbox per job for selective application
- **Job Details Modal**: Full job description view

**Technical Integration**:
- Uses `src/agent/job_matcher.py` for Claude API scoring
- Displays results from `src/storage/database.py`
- Uses `src/models/job.py` for data structure

**UI Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ 📋 Matched Jobs (47 found, 32 above threshold)              │
├─────────────────────────────────────────────────────────────┤
│ Sort: [Match Score ▼]  Filter: [Score > 60] [Easy Apply]    │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ☑ Chief of Staff                         Score: 92 🟢  │ │
│ │   TechStartup Inc. • New York, NY • 25 employees       │ │
│ │   Posted 2 days ago • Easy Apply ⚡                     │ │
│ │   ▼ View Match Justification                           │ │
│ │   ┌───────────────────────────────────────────────────┐ │ │
│ │   │ ✅ Strong match: 5+ years operations experience   │ │ │
│ │   │ ✅ MBA from target school                         │ │ │
│ │   │ ✅ Startup experience (Series A)                  │ │ │
│ │   │ ⚠️ Consider: Role requires fintech background     │ │ │
│ │   └───────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ☐ Director of Operations                 Score: 78 🟡  │ │
│ │   AI Health Co. • Remote • 85 employees               │ │
│ │   Posted 5 days ago • Easy Apply ⚡                    │ │
│ │   ▶ View Match Justification                          │ │
│ └─────────────────────────────────────────────────────────┘ │
│                        ... more jobs ...                    │
├─────────────────────────────────────────────────────────────┤
│ Selected: 5 jobs                                            │
│ [ Apply to Selected (5) ]  [ Apply to All (32) ]           │
└─────────────────────────────────────────────────────────────┘
```

---

### 4. Application Control & Tracking Page

**Purpose**: Control Easy Apply automation and track applications

**Features**:
- **Rate Limit Dashboard**:
  - Applications today: X / 25
  - Progress bar showing daily limit
  - Estimated time to complete queue
  - Cool-down timer display
- **Application Queue**:
  - Jobs pending application
  - Drag-to-reorder priority
  - Remove from queue button
- **Live Application Status**:
  - Currently applying to: [Job Title] @ [Company]
  - Progress indicator
  - Real-time log of actions
- **Controls**:
  - Start / Pause / Stop buttons
  - Delay settings (min/max seconds between applications)
  - Dry-run mode toggle (preview without applying)
- **Application History**:
  - List of completed applications
  - Status: Submitted, Viewed, Rejected, Interview
  - Timestamp and notes
  - Export to CSV

**Technical Integration**:
- Uses `src/agent/applicant.py` for Easy Apply automation
- Uses `src/browser/linkedin_browser.py` for browser control
- Persists to `src/storage/database.py`
- Uses `src/models/application.py` for tracking

**UI Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ 🚀 Application Control                                      │
├─────────────────────────────────────────────────────────────┤
│ Today's Applications: 12 / 25                               │
│ [████████████░░░░░░░░░░░░] 48%                             │
│ Rate: ~45 seconds between applications                      │
├─────────────────────────────────────────────────────────────┤
│ Queue: 5 jobs pending                                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 1. Chief of Staff @ TechStartup Inc. (Score: 92)    [x]│ │
│ │ 2. BizOps Lead @ AI Health Co. (Score: 85)          [x]│ │
│ │ 3. Director of Ops @ FinanceAI (Score: 78)          [x]│ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ Status: ● Applying to "Chief of Staff @ TechStartup Inc."  │
│ [Filling form...] ████████░░ 80%                           │
├─────────────────────────────────────────────────────────────┤
│ ☐ Dry Run Mode (preview only)                              │
│ Delay: [30] - [90] seconds                                 │
│                                                             │
│   [ ▶ Start ]  [ ⏸ Pause ]  [ ⏹ Stop ]                     │
├─────────────────────────────────────────────────────────────┤
│ 📜 Application Log:                                         │
│ [14:32:05] ✅ Applied to "BizOps Lead @ AI Health Co."     │
│ [14:31:20] 🔄 Filling application form...                  │
│ [14:30:45] 📝 Opening job listing...                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Foundation & Resume Page

**Tasks**:
1. Set up Streamlit project structure in `src/ui/`
2. Create main app entry point (`app.py`)
3. Implement session state management
4. Build resume upload component with drag-and-drop
5. Integrate existing `resume/parser.py` for PDF/JSON parsing
6. Display parsed profile with sections
7. Add resume validation and error handling

**Deliverables**:
- Working resume upload and preview
- Profile persistence to session state
- Basic navigation structure

**Dependencies**:
- Existing `src/resume/` module (✅ complete)

---

### Phase 2: Search Configuration Page

**Tasks**:
1. Build search criteria form components
2. Create location/title multi-select with custom input
3. Implement filter toggles (experience, company size, etc.)
4. Add exclusion rules configuration
5. Create search preset save/load functionality
6. Connect to search criteria model

**Deliverables**:
- Complete search configuration interface
- Persistence to YAML config
- Form validation

**Dependencies**:
- Requires `src/models/search_criteria.py` (TODO: CORE agent)
- Requires `src/config.py` (TODO: CORE agent)

---

### Phase 3: Job Results & Matching Page

**Tasks**:
1. Build job card component with all fields
2. Create match score visualization (color-coded)
3. Implement expandable justification panel
4. Add sorting and filtering controls
5. Build job selection mechanism (checkboxes)
6. Create job details modal
7. Integrate with job matching service

**Deliverables**:
- Job results display with match scores
- AI justification visibility
- Job selection for application

**Dependencies**:
- Requires `src/agent/job_matcher.py` (TODO: MATCHING agent)
- Requires `src/agent/job_searcher.py` (TODO: BROWSER agent)
- Requires `src/models/job.py` (TODO: CORE agent)

---

### Phase 4: Application Control Page

**Tasks**:
1. Build rate limit dashboard with progress bar
2. Create application queue with reordering
3. Implement real-time status display
4. Add start/pause/stop controls
5. Build application history table
6. Add dry-run mode toggle
7. Implement delay configuration
8. Create export functionality (CSV)

**Deliverables**:
- Full application control interface
- Real-time status updates
- Application tracking and history

**Dependencies**:
- Requires `src/agent/applicant.py` (TODO: MATCHING agent)
- Requires `src/browser/linkedin_browser.py` (TODO: BROWSER agent)
- Requires `src/storage/database.py` (TODO: CORE agent)

---

### Phase 5: Integration & Polish

**Tasks**:
1. End-to-end integration testing
2. Error handling and user feedback (toasts, alerts)
3. Loading states and skeleton screens
4. Responsive design adjustments
5. Add keyboard shortcuts
6. Performance optimization
7. Add help tooltips and documentation
8. Create onboarding flow for first-time users

**Deliverables**:
- Polished, production-ready UI
- Comprehensive error handling
- User documentation

---

## Technical Specifications

### New Dependencies

Add to `requirements.txt`:
```txt
# UI Layer
streamlit>=1.30.0
streamlit-aggrid>=0.3.4     # Advanced data tables
streamlit-tags>=1.2.8       # Tag input for skills/titles
watchdog>=3.0.0             # File watching for hot reload
```

### Session State Schema

```python
# src/ui/services/session_state.py
from dataclasses import dataclass
from typing import Optional, List
from src.resume.profile import UserProfile
from src.models.job import Job
from src.models.search_criteria import SearchCriteria

@dataclass
class UISessionState:
    # Resume state
    profile: Optional[UserProfile] = None
    resume_file_path: Optional[str] = None

    # Search state
    search_criteria: Optional[SearchCriteria] = None

    # Results state
    matched_jobs: List[Job] = field(default_factory=list)
    selected_job_ids: List[str] = field(default_factory=list)

    # Application state
    application_queue: List[str] = field(default_factory=list)
    applications_today: int = 0
    is_applying: bool = False
    current_application: Optional[str] = None

    # Settings
    dry_run_mode: bool = False
    min_delay_seconds: int = 30
    max_delay_seconds: int = 90
    daily_limit: int = 25
```

### API Service Layer

```python
# src/ui/services/job_service.py
from typing import List, Tuple
from src.resume.profile import UserProfile
from src.models.job import Job
from src.models.search_criteria import SearchCriteria

class JobService:
    """Orchestrates job search and matching operations."""

    async def search_jobs(
        self,
        criteria: SearchCriteria
    ) -> List[Job]:
        """Execute job search with given criteria."""
        pass

    async def match_jobs(
        self,
        jobs: List[Job],
        profile: UserProfile
    ) -> List[Tuple[Job, int, str]]:
        """Score jobs against profile, return (job, score, justification)."""
        pass

    async def get_job_details(
        self,
        job_id: str
    ) -> Job:
        """Fetch full job description."""
        pass
```

```python
# src/ui/services/apply_service.py
from typing import AsyncGenerator
from src.models.job import Job
from src.models.application import Application

class ApplyService:
    """Handles application submission with rate limiting."""

    def __init__(
        self,
        daily_limit: int = 25,
        min_delay: int = 30,
        max_delay: int = 90,
        dry_run: bool = False
    ):
        self.daily_limit = daily_limit
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.dry_run = dry_run

    async def apply_to_job(
        self,
        job: Job,
        profile: UserProfile
    ) -> Application:
        """Submit application for a single job."""
        pass

    async def apply_to_queue(
        self,
        jobs: List[Job],
        profile: UserProfile
    ) -> AsyncGenerator[Application, None]:
        """Process application queue with rate limiting."""
        pass

    def get_remaining_applications(self) -> int:
        """Return how many applications can still be made today."""
        pass
```

---

## UI Configuration

### New Config File

```yaml
# config/ui_settings.yaml
ui:
  title: "Job Hunter"
  page_icon: "🎯"
  layout: "wide"
  theme:
    primaryColor: "#0077B5"  # LinkedIn blue
    backgroundColor: "#FFFFFF"
    secondaryBackgroundColor: "#F3F2EF"
    textColor: "#000000"

rate_limits:
  daily_max_applications: 25
  min_delay_seconds: 30
  max_delay_seconds: 90
  pause_between_searches_minutes: 5

defaults:
  min_match_score: 60
  easy_apply_only: true
  experience_levels:
    - "Mid-Senior level"
    - "Senior level"
  company_sizes:
    - "1-10 employees"
    - "11-50 employees"
    - "51-200 employees"
```

---

## Streamlit Main App Structure

```python
# src/ui/app.py
import streamlit as st

st.set_page_config(
    page_title="Job Hunter",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("🎯 Job Hunter")
st.sidebar.markdown("---")

# Navigation state
if 'profile' not in st.session_state:
    st.sidebar.warning("⚠️ No resume uploaded")
else:
    st.sidebar.success(f"✅ {st.session_state.profile.contact.name}")

# Rate limit indicator in sidebar
if 'applications_today' in st.session_state:
    progress = st.session_state.applications_today / 25
    st.sidebar.progress(progress, text=f"Applications: {st.session_state.applications_today}/25")

# Main content - handled by page files
st.title("Welcome to Job Hunter")
st.markdown("""
Use the sidebar to navigate:
1. **Resume** - Upload and manage your resume
2. **Search** - Configure job search criteria
3. **Results** - View matched jobs with AI justifications
4. **Applications** - Control and track your applications
""")
```

---

## Real-time Updates Architecture

For live application status updates, use Streamlit's session state with auto-refresh:

```python
# In application page
import time

# Status container that updates
status_container = st.empty()

if st.session_state.is_applying:
    with status_container.container():
        st.markdown(f"**Currently applying to:** {st.session_state.current_application}")
        st.progress(st.session_state.application_progress)

    # Auto-refresh every 2 seconds while applying
    time.sleep(2)
    st.rerun()
```

For more advanced real-time updates (FastAPI version), use WebSocket:

```python
# Backend: FastAPI WebSocket endpoint
@app.websocket("/ws/application-status")
async def application_status(websocket: WebSocket):
    await websocket.accept()
    while True:
        status = await get_current_application_status()
        await websocket.send_json(status)
        await asyncio.sleep(1)
```

---

## Testing Strategy

### UI Component Tests

```python
# tests/test_ui/test_resume_page.py
import pytest
from streamlit.testing.v1 import AppTest

def test_resume_upload_displays_profile():
    """Test that uploading a resume displays parsed profile."""
    at = AppTest.from_file("src/ui/pages/1_resume.py")
    at.run()

    # Simulate file upload
    at.file_uploader[0].upload("tests/fixtures/sample_resume.pdf")
    at.run()

    # Verify profile is displayed
    assert "John Doe" in at.markdown[0].value
```

### Integration Tests

```python
# tests/test_ui/test_integration.py
def test_end_to_end_workflow():
    """Test complete workflow from upload to application."""
    # Upload resume
    # Configure search
    # View results
    # Select jobs
    # Start application (dry run)
    # Verify tracking
    pass
```

---

## Launch Commands

### Development

```bash
# Run Streamlit app in development mode
streamlit run src/ui/app.py --server.runOnSave true

# With custom port
streamlit run src/ui/app.py --server.port 8080
```

### Production

```bash
# Run with production settings
streamlit run src/ui/app.py \
  --server.headless true \
  --server.enableCORS false \
  --server.enableXsrfProtection true \
  --server.maxUploadSize 10
```

### Add to CLI

```python
# In src/main.py
@app.command()
def ui(
    port: int = typer.Option(8501, help="Port to run UI on"),
    debug: bool = typer.Option(False, help="Enable debug mode")
):
    """Launch the web UI."""
    import subprocess
    cmd = ["streamlit", "run", "src/ui/app.py", "--server.port", str(port)]
    if not debug:
        cmd.append("--server.headless=true")
    subprocess.run(cmd)
```

---

## Security Considerations

1. **Credential Storage**: LinkedIn credentials should use secure storage (keyring/env vars), never exposed in UI
2. **Session Security**: Use Streamlit's session state isolation
3. **File Upload Validation**: Validate file types and sizes for resume uploads
4. **Rate Limiting**: Enforce server-side rate limits, not just UI display
5. **No Credential Display**: Never show passwords or API keys in UI

---

## Summary

| Phase | Focus | Key Deliverables | Dependencies |
|-------|-------|------------------|--------------|
| 1 | Foundation & Resume | Resume upload, parsing, preview | Resume module (✅) |
| 2 | Search Config | Search form, filters, presets | Config, SearchCriteria models |
| 3 | Results & Matching | Job cards, scores, justifications | JobMatcher, Job models |
| 4 | Application Control | Queue, rate limits, tracking | Applicant, Browser, Database |
| 5 | Polish | Error handling, UX, testing | All modules complete |

---

## Next Steps

1. **Immediate**: Implement Phase 1 (Resume page) using existing `src/resume/` module
2. **Parallel**: Other agents complete CORE, BROWSER, and MATCHING modules
3. **Iterative**: Build remaining UI phases as dependencies become available
4. **Optional**: Migrate to FastAPI + React for production-grade UI
