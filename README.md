# LinkedIn Job Application Agent - Matching Module

Intelligent job matching and application engine powered by Claude API.

## Overview

This module provides LLM-powered job matching and Easy Apply automation for LinkedIn job searches. It uses a two-stage filtering approach:

1. **Keyword Filtering** - Fast, cost-free initial filtering based on keywords, location, company size
2. **LLM Scoring** - Claude API analyzes job-resume fit and provides 0-100 match score with reasoning

## Features

- **Smart Matching**: Uses Claude API to intelligently score job-resume fit
- **Keyword Filtering**: Pre-filters jobs to reduce API costs
- **Custom Question Answering**: Generates contextual answers to application questions
- **Easy Apply Automation**: Automates LinkedIn Easy Apply form submission
- **Rate Limiting**: Human-like delays and application limits
- **Comprehensive Logging**: Track all matching decisions and applications

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials
```

## Configuration

### Environment Variables

Create a `.env` file with:

```bash
ANTHROPIC_API_KEY=your-claude-api-key
LINKEDIN_EMAIL=your-email
LINKEDIN_PASSWORD=your-password
MIN_MATCH_SCORE=60
```

### Search Criteria

The `SearchCriteria` model (src/models/search_criteria.py) defines matching preferences:

```python
criteria = SearchCriteria(
    titles=["Chief of Staff", "Business Operations", "BizOps"],
    locations=["New York, NY", "San Francisco, CA", "Remote"],
    excluded_locations=["Israel"],
    company_sizes=["1-10 employees", "11-50 employees", "51-200 employees"],
    min_match_score=60,
    max_applications_per_day=25,
)
```

## Usage

### Basic Matching

```python
from src.agent.job_matcher import JobMatcher
from src.models.search_criteria import SearchCriteria
from src.resume.profile import UserProfile
from src.models.job import Job

# Load your profile
profile = UserProfile(
    full_name="Your Name",
    email="you@example.com",
    skills=["Strategic Planning", "Business Operations"],
    # ... more profile fields
)

# Create criteria
criteria = SearchCriteria()

# Initialize matcher
matcher = JobMatcher(
    profile=profile,
    criteria=criteria,
    api_key="your-api-key"
)

# Match a job
job = Job(
    linkedin_job_id="12345",
    title="Chief of Staff",
    company="Awesome Startup",
    location="New York, NY",
    description="...",
)

# Run matching pipeline
updated_job, is_match = matcher.match_job(job)

if is_match:
    print(f"Match! Score: {updated_job.match_score}/100")
    print(f"Reasoning: {updated_job.match_reasoning}")
else:
    print(f"No match. Score: {updated_job.match_score}/100")
```

### Answering Custom Questions

```python
question = "Why are you interested in this role?"
answer = matcher.answer_application_question(question)
print(answer)
```

### Easy Apply Automation

```python
from playwright.sync_api import sync_playwright
from src.agent.applicant import EasyApplyBot

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    # Login to LinkedIn (implementation needed)
    # ...

    # Create bot
    bot = EasyApplyBot(
        page=page,
        profile=profile,
        matcher=matcher,
    )

    # Apply to matched job
    application = bot.apply_to_job(job)

    print(f"Application submitted: {application.submitted_at}")
```

## Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_matching.py

# Run specific test
pytest tests/test_matching.py::TestJobMatcher::test_keyword_filter_good_match
```

## Architecture

### Two-Stage Matching

```
Job Input
    ↓
Keyword Filter (Fast, Free)
    ├─ Location check
    ├─ Company size check
    ├─ Keyword matches
    ↓
LLM Scoring (Smart, API cost)
    ├─ Claude API analysis
    ├─ Score 0-100
    ├─ Match reasoning
    ↓
Match Decision (score >= threshold)
```

### Key Components

- **JobMatcher** (src/agent/job_matcher.py)
  - `keyword_filter()` - Fast pre-filtering
  - `score_job_match()` - Claude API scoring
  - `answer_application_question()` - Generate answers
  - `match_job()` - Complete pipeline

- **EasyApplyBot** (src/agent/applicant.py)
  - `apply_to_job()` - Submit application
  - Form navigation and filling
  - Custom question handling
  - Rate limiting

### Models

- **Job** - Job posting data with match metadata
- **UserProfile** - Resume/profile information
- **SearchCriteria** - Matching preferences
- **MatchResult** - Scoring results
- **Application** - Application tracking

## Matching Criteria

### Default Filters

- **Location**: Excludes specified locations (e.g., Israel)
- **Company Size**: Filters to startup sizes (1-200 employees)
- **Keywords**: Requires minimum 2 profile keyword matches
- **Excluded Keywords**: Filters out unwanted terms

### LLM Scoring Criteria

Claude evaluates:

1. **Role Alignment** - Chief of Staff / BizOps focus
2. **Skills Match** - Technical and soft skills alignment
3. **Experience Fit** - Mid to senior level experience
4. **Company Stage** - Seed to Series A indicators
5. **Location Fit** - Preference matching

### Score Interpretation

- **80-100**: Excellent match - highly recommended
- **60-79**: Good match - worth applying
- **40-59**: Moderate match - review manually
- **0-39**: Poor match - skip

## Cost Optimization

To minimize Claude API costs:

1. **Keyword filter first** - Reduces LLM calls by ~80%
2. **Cache results** - Store match scores in database
3. **Batch processing** - Process jobs in groups
4. **Adjust threshold** - Higher min_match_score = fewer applications = lower cost

Estimated costs (with keyword pre-filtering):
- ~100 jobs searched → ~20 jobs scored → $0.10-0.30
- Daily usage (25 applications) → ~$0.50-1.00/day

## Safety & Rate Limiting

Built-in protections:

- **Application Limits**: Max 25 applications/day (configurable)
- **Random Delays**: 30-90 seconds between applications
- **Human-like Behavior**: Typing delays, mouse movements
- **Error Handling**: Graceful failures, detailed logging

## Logging

Configure logging in your application:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

Log levels:
- **DEBUG**: Detailed matching decisions, API calls
- **INFO**: Match results, applications submitted
- **WARNING**: Rate limiting, recoverable errors
- **ERROR**: Application failures, API errors

## Integration with Other Modules

This matching module integrates with:

- **CORE Module**: Uses Job, SearchCriteria models and database
- **RESUME Module**: Requires UserProfile for matching
- **BROWSER Module**: Provides Page object for EasyApplyBot

## Future Enhancements

Potential improvements:

- [ ] Parallel job scoring for speed
- [ ] Match quality learning from user feedback
- [ ] Cover letter generation
- [ ] Interview preparation tips based on job
- [ ] Application status tracking and follow-ups

## Troubleshooting

### API Key Issues

```
ValueError: Anthropic API key required
```
→ Set `ANTHROPIC_API_KEY` in .env file

### Low Match Scores

If all jobs score low:
- Review profile completeness
- Check keyword filtering isn't too strict
- Lower `min_match_score` threshold
- Add more relevant skills to profile

### Application Failures

- Check LinkedIn login status
- Verify Easy Apply is available
- Review selector compatibility (LinkedIn may change UI)
- Check rate limiting hasn't triggered

## License

See LICENSE file in project root.

## Support

For issues or questions, see CLAUDE.md for agent coordination notes.
