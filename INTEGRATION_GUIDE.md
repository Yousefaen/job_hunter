# Integration Guide - Connecting MATCHING Agent with Other Agents

## Overview

This guide explains how the MATCHING agent integrates with other agents (CORE, BROWSER, RESUME) to form the complete LinkedIn Job Hunter system.

## Current Status

### ✅ MATCHING Agent (Completed)

**What's Ready:**
- JobMatcher with keyword filtering and LLM scoring
- EasyApplyBot for form automation
- All data models (Job, UserProfile, SearchCriteria, Application)
- Custom question answering
- Comprehensive test suite
- Full documentation

**What it Provides:**
- `JobMatcher` class - Score jobs and answer questions
- `EasyApplyBot` class - Automate applications
- Data models - Shared across all agents
- Test fixtures - Reusable for integration tests

### 🔲 CORE Agent (Needed)

**What MATCHING Needs from CORE:**
1. **Database Layer** (`src/storage/database.py`)
   ```python
   class JobDatabase:
       def save_job(job: Job) -> None
       def get_job(job_id: str) -> Job
       def get_all_jobs(status: JobStatus = None) -> List[Job]
       def update_job(job: Job) -> None

       def save_application(app: Application) -> None
       def get_applications(job_id: str = None) -> List[Application]
       def get_daily_application_count() -> int
   ```

2. **Configuration Management** (`src/config.py`)
   ```python
   class Config:
       def load_profile() -> UserProfile
       def load_criteria() -> SearchCriteria
       def get_api_key() -> str
   ```

3. **CLI Interface** (`src/main.py`)
   ```python
   # Commands needed:
   # - search: Find jobs
   # - match: Score a specific job
   # - apply: Apply to matched jobs
   # - status: Show application status
   ```

### 🔲 BROWSER Agent (Needed)

**What MATCHING Needs from BROWSER:**
1. **Playwright Page Object** (for EasyApplyBot)
   ```python
   from playwright.sync_api import Page

   # BROWSER agent must provide:
   page: Page  # Already logged into LinkedIn
   ```

2. **Job Scraping** (`src/agent/job_searcher.py`)
   ```python
   class JobSearcher:
       def search_jobs(criteria: SearchCriteria) -> List[Job]
       def get_job_details(job_id: str) -> Job
   ```

**What MATCHING Provides to BROWSER:**
- `EasyApplyBot` accepts Page object from BROWSER
- Application submission functionality

### 🔲 RESUME Agent (Needed)

**What MATCHING Needs from RESUME:**
1. **Resume Parser** (`src/resume/parser.py`)
   ```python
   class ResumeParser:
       def parse_pdf(pdf_path: str) -> UserProfile
       def parse_json(json_path: str) -> UserProfile
   ```

**What MATCHING Provides to RESUME:**
- `UserProfile` model (already complete)
- Profile validation via Pydantic

## Integration Examples

### Example 1: Full Job Matching Pipeline

```python
"""Complete pipeline from search to application."""

from src.agent.job_matcher import JobMatcher
from src.agent.applicant import EasyApplyBot
from src.agent.job_searcher import JobSearcher  # From BROWSER
from src.resume.parser import ResumeParser  # From RESUME
from src.storage.database import JobDatabase  # From CORE
from src.config import Config  # From CORE

# 1. Load configuration (CORE)
config = Config.load()
profile = config.load_profile()  # or ResumeParser.parse_pdf("resume.pdf")
criteria = config.load_criteria()

# 2. Initialize database (CORE)
db = JobDatabase()

# 3. Search for jobs (BROWSER)
searcher = JobSearcher()
jobs = searcher.search_jobs(criteria)
print(f"Found {len(jobs)} jobs")

# 4. Match jobs (MATCHING)
matcher = JobMatcher(profile, criteria)
matched_jobs = []

for job in jobs:
    updated_job, is_match = matcher.match_job(job)
    db.save_job(updated_job)  # Save with match data

    if is_match:
        matched_jobs.append(updated_job)

print(f"Matched {len(matched_jobs)} jobs")

# 5. Apply to matched jobs (MATCHING + BROWSER)
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    # Login to LinkedIn (BROWSER handles this)
    # ...

    # Create bot
    bot = EasyApplyBot(page, profile, matcher)

    # Apply to jobs
    for job in matched_jobs[:25]:  # Max 25 per day
        try:
            if db.get_daily_application_count() >= 25:
                print("Daily limit reached")
                break

            application = bot.apply_to_job(job)
            db.save_application(application)

            print(f"✓ Applied to {job.title} at {job.company}")
        except Exception as e:
            print(f"✗ Failed: {e}")

    browser.close()
```

### Example 2: CLI Integration

```python
"""CLI commands using all agents."""

import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command()
def search(
    titles: str = "Chief of Staff,BizOps",
    location: str = "New York, NY",
    max_results: int = 100,
):
    """Search for jobs and score matches."""
    # Load config (CORE)
    config = Config.load()
    profile = config.load_profile()
    criteria = config.load_criteria()

    # Search (BROWSER)
    searcher = JobSearcher()
    jobs = searcher.search_jobs(criteria)

    # Match (MATCHING)
    matcher = JobMatcher(profile, criteria)
    db = JobDatabase()

    for job in jobs[:max_results]:
        updated_job, is_match = matcher.match_job(job)
        db.save_job(updated_job)

        if is_match:
            console.print(f"✅ [green]{job.title}[/green] at {job.company} "
                         f"(Score: {updated_job.match_score}/100)")

@app.command()
def apply(job_id: str = None, auto: bool = False):
    """Apply to matched jobs."""
    db = JobDatabase()

    if job_id:
        jobs = [db.get_job(job_id)]
    else:
        jobs = db.get_all_jobs(status=JobStatus.MATCHED)

    if not auto:
        # Show preview and confirm
        console.print(f"Ready to apply to {len(jobs)} jobs. Continue? [y/n]")
        if input().lower() != 'y':
            return

    # Apply (MATCHING + BROWSER)
    config = Config.load()
    profile = config.load_profile()
    matcher = JobMatcher(profile, config.load_criteria())

    with sync_playwright() as p:
        page = setup_browser(p)  # BROWSER helper
        bot = EasyApplyBot(page, profile, matcher)

        for job in jobs:
            try:
                app = bot.apply_to_job(job)
                db.save_application(app)
                console.print(f"✅ Applied to {job.title}")
            except Exception as e:
                console.print(f"❌ Failed: {e}")

@app.command()
def status():
    """Show application status."""
    db = JobDatabase()

    stats = {
        "total_found": len(db.get_all_jobs()),
        "matched": len(db.get_all_jobs(JobStatus.MATCHED)),
        "applied": len(db.get_all_jobs(JobStatus.APPLIED)),
        "interviewing": len(db.get_all_jobs(JobStatus.INTERVIEWING)),
    }

    console.print("📊 Application Statistics:")
    for key, value in stats.items():
        console.print(f"  {key}: {value}")
```

### Example 3: Testing Integration

```python
"""Integration tests across agents."""

import pytest
from playwright.sync_api import sync_playwright

def test_full_application_flow():
    """Test complete flow from search to application."""
    # Setup (CORE)
    config = Config.load()
    db = JobDatabase(":memory:")  # In-memory for testing

    # Create test profile (RESUME)
    profile = create_test_profile()
    criteria = SearchCriteria()

    # Mock job search (BROWSER would provide this)
    test_job = Job(
        linkedin_job_id="test-123",
        title="Chief of Staff",
        company="Test Startup",
        location="New York, NY",
        description="Great opportunity...",
        company_size="11-50 employees",
        easy_apply=True,
    )

    # Test matching (MATCHING)
    matcher = JobMatcher(profile, criteria, api_key="test-key")
    updated_job, is_match = matcher.match_job(test_job)

    assert is_match is True or is_match is False  # Should return bool
    assert updated_job.match_score is not None
    assert updated_job.status in [JobStatus.MATCHED, JobStatus.REJECTED]

    # If matched, test application (MATCHING + BROWSER)
    if is_match:
        # Note: This would require a test LinkedIn environment
        # or mocking Playwright interactions
        pass
```

## Database Schema

The CORE agent should implement these tables:

```sql
-- Jobs table
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    linkedin_job_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT NOT NULL,
    description TEXT,
    company_size TEXT,
    experience_level TEXT,
    easy_apply BOOLEAN,
    status TEXT NOT NULL,
    match_score INTEGER,
    match_reasoning TEXT,
    found_at TIMESTAMP,
    matched_at TIMESTAMP,
    applied_at TIMESTAMP
);

-- Applications table
CREATE TABLE applications (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    status TEXT NOT NULL,
    submitted_at TIMESTAMP,
    custom_questions JSON,
    notes TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(linkedin_job_id)
);

-- User profile table (optional - could use file)
CREATE TABLE user_profile (
    id TEXT PRIMARY KEY,
    profile_data JSON NOT NULL,
    updated_at TIMESTAMP
);
```

## Configuration Files

### config/settings.yaml (CORE should create)

```yaml
# Application settings
anthropic:
  api_key: ${ANTHROPIC_API_KEY}  # From environment
  model: claude-3-5-sonnet-20241022

linkedin:
  email: ${LINKEDIN_EMAIL}
  password: ${LINKEDIN_PASSWORD}

# Matching settings
matching:
  min_score: 60
  max_applications_per_day: 25
  min_delay_seconds: 30
  max_delay_seconds: 90

# Paths
paths:
  resume: data/resumes/resume.pdf
  database: data/job_hunter.db
  logs: logs/

# Logging
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### config/search_criteria.yaml (CORE should create)

```yaml
# Job search criteria
titles:
  - Chief of Staff
  - Business Operations
  - BizOps
  - Head of Business Operations
  - Director of Operations

locations:
  - New York, NY
  - New York City Metropolitan Area
  - Palo Alto, CA
  - San Francisco Bay Area
  - Remote

excluded_locations:
  - Israel

experience_levels:
  - Mid-Senior level
  - Senior level

job_types:
  - Full-time

company_sizes:
  - 1-10 employees
  - 11-50 employees
  - 51-200 employees

# Additional filters
date_posted: Past week
easy_apply_only: true

# Keywords
required_keywords: []
excluded_keywords:
  - insurance
  - sales
```

## Shared Utilities

These utilities would be useful across all agents:

```python
# src/utils/logger.py
import logging

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Create configured logger."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

# src/utils/rate_limiter.py
import time
import random

class RateLimiter:
    """Simple rate limiter with random delays."""

    def __init__(self, min_delay: int = 30, max_delay: int = 90):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_action = 0

    def wait(self):
        """Wait appropriate amount of time."""
        now = time.time()
        elapsed = now - self.last_action
        delay = random.randint(self.min_delay, self.max_delay)

        if elapsed < delay:
            time.sleep(delay - elapsed)

        self.last_action = time.time()
```

## Agent Communication Protocol

```python
"""Standard way for agents to communicate."""

from typing import Protocol, List

class JobProvider(Protocol):
    """Interface for providing jobs (BROWSER agent)."""

    def search_jobs(self, criteria: SearchCriteria) -> List[Job]:
        """Search for jobs matching criteria."""
        ...

class JobMatcher(Protocol):
    """Interface for matching jobs (MATCHING agent)."""

    def match_job(self, job: Job) -> tuple[Job, bool]:
        """Score and match a job."""
        ...

class JobApplicant(Protocol):
    """Interface for applying to jobs (MATCHING agent)."""

    def apply_to_job(self, job: Job) -> Application:
        """Submit application to job."""
        ...

class JobStorage(Protocol):
    """Interface for storing jobs (CORE agent)."""

    def save_job(self, job: Job) -> None:
        """Save job to database."""
        ...

    def get_jobs(self, status: JobStatus = None) -> List[Job]:
        """Retrieve jobs from database."""
        ...
```

## Next Steps for Integration

### For CORE Agent:
1. Implement `src/storage/database.py` with SQLite
2. Implement `src/config.py` for YAML config loading
3. Create `src/main.py` with Typer CLI
4. Create config file templates

### For BROWSER Agent:
1. Implement `src/agent/job_searcher.py` for LinkedIn scraping
2. Implement `src/browser/linkedin_browser.py` for browser setup
3. Implement `src/browser/login.py` for authentication
4. Provide Page object to MATCHING agent

### For RESUME Agent:
1. Implement `src/resume/parser.py` for PDF parsing
2. Extract data into UserProfile format
3. Support JSON profile format as alternative

### For All Agents:
1. Follow shared data models from MATCHING agent
2. Use consistent error handling patterns
3. Share test fixtures from `tests/conftest.py`
4. Coordinate on logging standards

## Testing Integration

```bash
# Once all agents are ready:

# 1. Test CORE + MATCHING
pytest tests/test_integration_core_matching.py

# 2. Test BROWSER + MATCHING
pytest tests/test_integration_browser_matching.py

# 3. Test RESUME + MATCHING
pytest tests/test_integration_resume_matching.py

# 4. Test full system
pytest tests/test_integration_full_system.py
```

## Documentation

Each agent should maintain:
- README.md - Overview and usage
- ARCHITECTURE.md - Technical design
- API.md - Public interface documentation
- CHANGELOG.md - Version history

## Conclusion

The MATCHING agent is fully functional and ready to integrate. It provides:
- Complete data models (use as shared interfaces)
- Production-ready matching logic
- Application automation
- Comprehensive tests

Next: Implement CORE, BROWSER, and RESUME agents using this integration guide.
