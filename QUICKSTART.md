# Quick Start Guide

Get the matching module up and running in minutes.

## Prerequisites

- Python 3.11 or higher
- pip package manager

## Installation

### 1. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Set Up Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your credentials
# Required: ANTHROPIC_API_KEY
# Optional: LINKEDIN_EMAIL, LINKEDIN_PASSWORD (for automation)
```

Get your Anthropic API key from: https://console.anthropic.com/

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_matching.py
```

## Quick Test

### Option 1: Run Example Script

```bash
# Make sure ANTHROPIC_API_KEY is set in .env
python examples/usage_example.py
```

This will:
- Create a sample profile
- Test 3 different jobs (good match, poor match, excluded location)
- Show match scores and reasoning
- Generate answers to application questions

### Option 2: Interactive Python Session

```python
import os
from src.agent.job_matcher import JobMatcher
from src.models.job import Job
from src.models.search_criteria import SearchCriteria
from src.resume.profile import UserProfile

# Set API key
os.environ["ANTHROPIC_API_KEY"] = "your-key-here"

# Create minimal profile
profile = UserProfile(
    full_name="Your Name",
    email="you@example.com",
    summary="Business operations leader with startup experience",
    skills=["Strategic Planning", "Business Operations"],
)

# Create criteria
criteria = SearchCriteria()

# Initialize matcher
matcher = JobMatcher(profile, criteria)

# Test a job
job = Job(
    linkedin_job_id="test-123",
    title="Chief of Staff",
    company="Startup Inc",
    location="New York, NY",
    description="Chief of Staff at early-stage startup...",
    company_size="11-50 employees",
)

# Match it
updated_job, is_match = matcher.match_job(job)
print(f"Match: {is_match}, Score: {updated_job.match_score}/100")
print(f"Reasoning: {updated_job.match_reasoning}")
```

## What's Next?

1. **Customize Your Profile**: Edit the profile in `examples/usage_example.py` or create your own
2. **Adjust Criteria**: Modify `SearchCriteria` for your job preferences
3. **Test Matching**: Run against real job postings
4. **Integrate**: Connect with BROWSER and CORE modules for full automation

## Troubleshooting

### Import Errors

```
ModuleNotFoundError: No module named 'anthropic'
```
→ Run `pip install -r requirements.txt`

### API Key Errors

```
ValueError: Anthropic API key required
```
→ Set `ANTHROPIC_API_KEY` in `.env` file

### Playwright Errors

```
playwright._impl._api_types.Error: Browser not found
```
→ Run `playwright install chromium`

## Project Structure

```
matching/
├── src/
│   ├── agent/
│   │   ├── job_matcher.py      # Core matching logic
│   │   └── applicant.py        # Easy Apply automation
│   ├── models/
│   │   ├── job.py              # Job model
│   │   ├── search_criteria.py  # Search config
│   │   └── application.py      # Application tracking
│   └── resume/
│       └── profile.py          # User profile model
├── tests/
│   ├── conftest.py             # Test fixtures
│   └── test_matching.py        # Unit tests
├── examples/
│   └── usage_example.py        # Working example
├── requirements.txt            # Dependencies
└── README.md                   # Full documentation
```

## Cost Estimation

With keyword pre-filtering, expect:
- ~$0.10-0.30 per 100 jobs searched
- ~$0.50-1.00 per day (25 applications)

The keyword filter reduces LLM calls by ~80%, saving significant costs.

## Support

- Full documentation: See [README.md](README.md)
- Agent coordination: See [CLAUDE.md](CLAUDE.md)
- Implementation plan: See [PLAN.md](PLAN.md)
