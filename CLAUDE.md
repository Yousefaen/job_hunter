# LinkedIn Job Application Agent - Project Context

## Project Overview

Building an intelligent agent that automates job searching and application on LinkedIn for Chief of Staff / BizOps roles at early-stage startups (Seed to Series A).

## User Profile

- **Target Roles**: Chief of Staff, Business Operations, BizOps, Head of Business Operations, Director of Operations
- **Locations**: New York, Palo Alto/Bay Area, Remote
- **Experience Level**: Mid to Senior
- **Company Stage**: Seed to Series A (1-200 employees as proxy)
- **Exclusions**: Israel-based companies
- **Resume**: PDF available (user will provide)

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Browser Automation | Playwright |
| LLM Integration | Anthropic Claude API |
| Database | SQLite |
| PDF Parsing | pdfplumber |
| Config | PyYAML + Pydantic |
| CLI | Typer + Rich |
| Testing | pytest |

## Project Structure

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
├── PLAN.md                     # Full implementation plan
├── CLAUDE.md                   # This file
└── README.md
```

## Development Guidelines

1. **Python Style**: Use type hints, docstrings, and follow PEP 8
2. **Error Handling**: Graceful degradation, informative error messages
3. **Logging**: Use Python's logging module with appropriate levels
4. **Testing**: Write pytest tests for all modules
5. **Config**: Use environment variables for secrets (API keys, credentials)

## Important Considerations

- LinkedIn TOS: This tool automates interactions - use responsibly with rate limiting
- Rate Limiting: Random delays 30-90 seconds between actions, max 25 applications/day
- Security: Never commit credentials, use .env files

---

# Agent-Specific Instructions

## Agent: CORE (feature/core-foundation)

**Your Focus**: Project foundation, configuration, database, and CLI

### Tasks
1. Create `pyproject.toml` with all dependencies
2. Create `requirements.txt`
3. Implement `src/config.py` - YAML config loading with Pydantic validation
4. Implement `src/models/` - All data models (Job, Application, SearchCriteria)
5. Implement `src/storage/` - SQLite database layer
6. Implement `src/main.py` - Typer CLI with commands: `search`, `apply`, `status`, `config`
7. Create `config/settings.yaml` and `config/search_criteria.yaml` templates

### Dependencies You Create
Other agents depend on your models and config system. Prioritize:
- `src/models/job.py` - Job model
- `src/models/search_criteria.py` - Search criteria model
- `src/config.py` - Config loading

---

## Agent: RESUME (feature/resume-parser)

**Your Focus**: Resume parsing and user profile management

### Tasks
1. Implement `src/resume/parser.py` - PDF parsing with pdfplumber
2. Implement `src/resume/profile.py` - UserProfile model with skills, experience, education
3. Create JSON profile schema as alternative to PDF
4. Extract: contact info, skills, work experience, education, summary
5. Write tests in `tests/test_resume.py`

### Key Features
- Parse PDF resumes into structured data
- Support JSON profile format as alternative
- Extract keywords for job matching
- Handle various resume formats gracefully

### Integration Points
- Your `UserProfile` will be used by the matching agent
- Profile data feeds into application form filling

---

## Agent: BROWSER (feature/browser-automation)

**Your Focus**: Playwright browser automation for LinkedIn

### Tasks
1. Implement `src/browser/linkedin_browser.py` - Browser setup with stealth mode
2. Implement `src/browser/login.py` - LinkedIn authentication with session persistence
3. Implement `src/browser/selectors.py` - CSS/XPath selectors for LinkedIn elements
4. Implement `src/agent/job_searcher.py` - Job search and listing extraction
5. Write tests in `tests/test_browser.py`

### Key Features
- Stealth mode to avoid detection (playwright-stealth)
- Session cookie persistence (avoid repeated logins)
- Human-like delays and mouse movements
- Job listing extraction (title, company, location, description, Easy Apply status)
- Pagination handling

### LinkedIn Selectors to Target
- Job search results container
- Individual job cards
- Job detail panel
- Easy Apply button
- Application form fields

### Safety Requirements
- Random delays between actions (30-90 seconds)
- Respect rate limits
- Graceful error handling for element not found

---

## Agent: MATCHING (feature/job-matching)

**Your Focus**: LLM-powered job matching and application engine

### Tasks
1. Implement `src/agent/job_matcher.py` - Claude API integration for job scoring
2. Implement `src/agent/applicant.py` - Easy Apply form automation
3. Implement keyword extraction and initial filtering
4. Create prompts for job-resume matching
5. Create prompts for answering custom application questions
6. Write tests in `tests/test_matching.py`

### Key Features
- Keyword-based initial filtering (fast, no API cost)
- Claude API scoring (0-100) with match explanation
- Filter by: company size, location, experience level
- Custom question answering based on resume context
- Application tracking and logging

### Matching Criteria
```yaml
min_match_score: 60
excluded_locations:
  - "Israel"
company_size:
  - "1-10 employees"
  - "11-50 employees"
  - "51-200 employees"
```

### Claude API Prompts Needed
1. **Job Match Scoring**: Given resume + job description, score fit 0-100 with reasoning
2. **Question Answering**: Given resume + question, generate appropriate answer

---

## Coordination Notes

- **Shared Models**: All agents should use models from `src/models/`
- **Config**: All agents should use `src/config.py` for configuration
- **Database**: All agents should use `src/storage/database.py` for persistence
- **Testing**: Each agent writes tests for their modules
- **Commits**: Use conventional commits (feat:, fix:, docs:, test:)

## Environment Variables (use .env file)

```
ANTHROPIC_API_KEY=your_api_key
LINKEDIN_EMAIL=your_email
LINKEDIN_PASSWORD=your_password
```

Never commit .env files!
