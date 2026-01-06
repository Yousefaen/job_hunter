# LinkedIn Job Application Agent - Implementation Plan

## Overview

Build an intelligent agent that automates job searching and application on LinkedIn based on user's resume and target role preferences.

## Key Decisions Needed

Before implementation, we need to decide on a few approaches:

### 1. Automation Approach

| Approach | Pros | Cons |
|----------|------|------|
| **Browser Automation (Playwright)** | Full control, can handle Easy Apply | Against LinkedIn TOS, requires careful rate limiting |
| **LinkedIn API** | Official, stable | Very limited - no job application endpoints |
| **Hybrid (API + Browser)** | Best of both worlds | Complex setup |

**Recommendation**: Playwright-based browser automation with respectful rate limiting and human-like delays.

### 2. Resume Handling

| Approach | Pros | Cons |
|----------|------|------|
| **PDF parsing** | Common format | Complex extraction |
| **JSON profile** | Easy to process | User must create it |
| **Both** | Flexibility | More code to maintain |

**Recommendation**: Support both PDF upload and a structured JSON profile format.

### 3. Job Matching

| Approach | Pros | Cons |
|----------|------|------|
| **Keyword matching** | Simple, fast, no API costs | May miss relevant jobs |
| **LLM-based matching** | Smart, context-aware | Requires API costs |
| **Hybrid scoring** | Balanced | More complex |

**Recommendation**: Hybrid approach - keyword matching for initial filtering, then Claude API for intelligent job-resume fit scoring and custom question answering.

---

## Proposed Architecture

```
job_hunter/
├── src/
│   ├── __init__.py
│   ├── main.py                 # CLI entry point
│   ├── config.py               # Configuration management
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── linkedin_agent.py   # Main agent orchestrator
│   │   ├── job_searcher.py     # Job search functionality
│   │   ├── job_matcher.py      # Resume-job matching logic
│   │   └── applicant.py        # Application submission
│   ├── browser/
│   │   ├── __init__.py
│   │   ├── linkedin_browser.py # Playwright browser automation
│   │   ├── login.py            # Authentication handling
│   │   └── selectors.py        # CSS/XPath selectors
│   ├── resume/
│   │   ├── __init__.py
│   │   ├── parser.py           # Resume parsing (PDF/JSON)
│   │   └── profile.py          # User profile model
│   ├── models/
│   │   ├── __init__.py
│   │   ├── job.py              # Job posting model
│   │   ├── application.py      # Application record model
│   │   └── search_criteria.py  # Search preferences model
│   └── storage/
│       ├── __init__.py
│       ├── database.py         # SQLite operations
│       └── schemas.py          # Database schemas
├── data/
│   ├── resumes/                # User resume storage
│   └── job_hunter.db           # SQLite database
├── config/
│   ├── settings.yaml           # Application settings
│   └── search_criteria.yaml    # Job search preferences
├── tests/
│   └── ...
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Implementation Phases

### Phase 1: Foundation (Core Setup)
- [ ] Project structure and dependencies setup
- [ ] Configuration system (YAML-based)
- [ ] SQLite database with models for jobs, applications
- [ ] Basic CLI interface

### Phase 2: Resume & Profile
- [ ] PDF resume parser using `pdfplumber` or `PyMuPDF`
- [ ] JSON profile schema definition
- [ ] Profile data model and validation

### Phase 3: LinkedIn Browser Automation
- [ ] Playwright browser setup with stealth mode
- [ ] LinkedIn login with session persistence
- [ ] Job search page navigation
- [ ] Job listing extraction/parsing
- [ ] Easy Apply form detection and filling

### Phase 4: Intelligent Matching
- [ ] Keyword extraction from resume (skills, experience, titles)
- [ ] Initial filtering based on keywords and criteria
- [ ] Claude API integration for deep job-resume fit scoring (0-100)
- [ ] Company size/stage filtering (proxy for seed/Series A)
- [ ] Location-based filtering (exclude Israel-based companies)
- [ ] Match reasoning/explanation from LLM
- [ ] Automatic filtering based on score threshold

### Phase 5: Application Engine
- [ ] Easy Apply form automation
- [ ] LLM-powered custom question answering (based on resume context)
- [ ] Application tracking and logging
- [ ] Rate limiting and human-like delays

### Phase 6: Polish & Safety
- [ ] Comprehensive error handling
- [ ] Retry logic with exponential backoff
- [ ] Daily application limits
- [ ] Detailed logging and reporting
- [ ] Dry-run mode for testing

---

## Core Features

### Job Search Criteria (Your Preferences)
```yaml
search_criteria:
  titles:
    - "Chief of Staff"
    - "Business Operations"
    - "BizOps"
    - "Head of Business Operations"
    - "Director of Operations"
  locations:
    - "New York, NY"
    - "New York City Metropolitan Area"
    - "Palo Alto, CA"
    - "San Francisco Bay Area"
    - "Remote"
  experience_level:
    - "Mid-Senior level"
    - "Senior level"
  job_type:
    - "Full-time"
  company_size:
    - "1-10 employees"      # Seed stage proxy
    - "11-50 employees"     # Seed/Series A proxy
    - "51-200 employees"    # Series A/B proxy
  date_posted: "Past week"
  easy_apply_only: true
  excluded_locations:
    - "Israel"              # Exclude Israel-based companies
  min_match_score: 60
```

### Target Company Profile
- **Stage**: Seed to Series A startups
- **Size**: 1-200 employees (as proxy for early stage)
- **Exclusions**: Israel-based companies

### Application Tracking
- Jobs found, matched, applied, rejected, interviewed
- Application timestamps and status updates
- Notes and follow-up reminders

### Safety Features
- Maximum applications per day (default: 25)
- Minimum delay between applications (default: 30-60 seconds)
- Human-like mouse movements and typing
- Session persistence to avoid repeated logins
- Dry-run mode to preview without applying

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Browser Automation | Playwright |
| LLM Integration | Anthropic Claude API |
| Database | SQLite |
| PDF Parsing | pdfplumber |
| Config | PyYAML |
| CLI | Typer |
| Testing | pytest |

---

## Dependencies

```txt
playwright>=1.40.0
anthropic>=0.18.0
pdfplumber>=0.10.0
pyyaml>=6.0
pydantic>=2.0
typer>=0.9.0
rich>=13.0.0
sqlite-utils>=3.35
```

---

## Important Considerations

### LinkedIn Terms of Service
- This tool automates LinkedIn interactions which may violate their TOS
- Use responsibly with appropriate rate limiting
- Consider this a personal productivity tool, not for commercial use
- LinkedIn may detect and restrict automated accounts

### Security
- LinkedIn credentials stored locally (never committed)
- Session cookies encrypted at rest
- API keys in environment variables

### Rate Limiting Strategy
- Random delays between actions (30-90 seconds)
- Maximum 25 applications per day
- Pause between job searches (5-10 minutes)
- Respect LinkedIn's implicit rate limits

---

## Your Profile Summary

| Setting | Value |
|---------|-------|
| **Target Roles** | Chief of Staff, BizOps at early-stage startups |
| **Company Stage** | Seed to Series A |
| **Locations** | New York, Palo Alto/Bay Area, Remote |
| **Experience Level** | Mid to Senior |
| **Exclusions** | Israel-based companies |
| **Resume** | PDF ready |
| **LLM Matching** | Enabled (Claude API) |

---

## Next Steps (Ready to Implement)

1. Set up project structure and dependencies
2. Implement configuration system
3. Build database models
4. Create resume parser
5. Implement LinkedIn browser automation
6. Add LLM-powered job matching (Claude API)
7. Build application engine with smart question answering
8. Add CLI interface
9. Write tests
10. Documentation
