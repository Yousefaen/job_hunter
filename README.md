# Job Hunter - LinkedIn Job Application Agent

An intelligent agent that automates job searching and application on LinkedIn for Chief of Staff / BizOps roles at early-stage startups (Seed to Series A).

## Overview

Job Hunter uses browser automation (Playwright) and AI-powered matching (Claude API) to streamline your job search process. It automatically finds relevant jobs, scores them based on your resume, and submits Easy Apply applications with intelligent question answering.

## Features

- **Intelligent Job Matching**: AI-powered scoring (0-100) based on resume fit
- **Easy Apply Automation**: Automated application submission
- **Smart Question Answering**: Claude API generates contextual answers
- **Rate Limiting**: Human-like delays and daily application limits
- **Application Tracking**: SQLite database tracks all jobs and applications
- **Flexible Configuration**: YAML-based settings for easy customization

## Tech Stack

- **Language**: Python 3.11+
- **Browser Automation**: Playwright
- **LLM Integration**: Anthropic Claude API
- **Database**: SQLite
- **PDF Parsing**: pdfplumber
- **Configuration**: PyYAML + Pydantic
- **CLI**: Typer + Rich
- **Testing**: pytest

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Yousefaen/job_hunter.git
cd job_hunter
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
playwright install chromium
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. Initialize configuration:
```bash
job-hunter init
```

## Configuration

### Environment Variables (.env)

Required:
- `ANTHROPIC_API_KEY`: Your Claude API key
- `LINKEDIN_EMAIL`: Your LinkedIn email
- `LINKEDIN_PASSWORD`: Your LinkedIn password

Optional:
- `DATABASE_PATH`: Path to SQLite database (default: data/job_hunter.db)
- `LOG_LEVEL`: Logging level (default: INFO)

### Search Criteria (config/search_criteria.yaml)

Customize your job search preferences:

```yaml
titles:
  - "Chief of Staff"
  - "Business Operations"
  - "BizOps"

locations:
  - "New York, NY"
  - "Palo Alto, CA"
  - "Remote"

company_sizes:
  - "1-10 employees"
  - "11-50 employees"
  - "51-200 employees"

min_match_score: 60.0
max_applications_per_day: 25
```

See `config/search_criteria.yaml` for all available options.

## Usage

### Search for Jobs

```bash
# Search LinkedIn and save matching jobs
job-hunter search

# Preview search without saving
job-hunter search --dry-run
```

### Apply to Jobs

```bash
# Apply to all qualified jobs
job-hunter apply

# Apply to at most 10 jobs
job-hunter apply --max 10

# Preview applications without submitting
job-hunter apply --dry-run
```

### Check Status

```bash
# View application statistics
job-hunter status

# Show detailed information
job-hunter status --verbose
```

### Manage Configuration

```bash
# View current configuration
job-hunter config

# Edit configuration files
job-hunter config --edit
```

## Project Structure

```
job_hunter/
├── src/
│   └── job_hunter/
│       ├── __init__.py
│       ├── main.py                 # CLI entry point
│       ├── config.py               # Configuration management
│       ├── agent/                  # Agent orchestration (BROWSER + MATCHING)
│       ├── browser/                # Playwright automation (BROWSER)
│       ├── resume/                 # Resume parsing (RESUME)
│       ├── models/                 # Data models ✅ COMPLETED
│       │   ├── job.py
│       │   ├── application.py
│       │   └── search_criteria.py
│       └── storage/                # Database layer ✅ COMPLETED
│           ├── database.py
│           └── schemas.py
├── config/
│   ├── settings.yaml               # Application settings ✅ COMPLETED
│   └── search_criteria.yaml        # Job search preferences ✅ COMPLETED
├── data/
│   ├── resumes/                    # User resume storage
│   └── job_hunter.db               # SQLite database
├── tests/
├── requirements.txt                # Dependencies ✅ COMPLETED
├── pyproject.toml                  # Project metadata ✅ COMPLETED
└── README.md                       # This file
```

## Core Agent Status ✅ COMPLETED

As the **CORE agent**, I have successfully implemented:

- ✅ Project structure and dependencies
- ✅ Configuration system with YAML and Pydantic validation
- ✅ Data models (Job, Application, SearchCriteria)
- ✅ SQLite database layer with full CRUD operations
- ✅ Typer-based CLI with commands: search, apply, status, config
- ✅ Configuration templates (settings.yaml, search_criteria.yaml)

### Dependencies Created for Other Agents

Other agents can now use:
- **Models**: `Job`, `Application`, `SearchCriteria` from `job_hunter.models`
- **Config**: `get_config()`, `Settings` from `job_hunter.config`
- **Database**: `Database` class from `job_hunter.storage`

## Other Agents

### BROWSER Agent (In Progress)
- LinkedIn browser automation
- Login and session management
- Job search and extraction
- Easy Apply form filling

### RESUME Agent (In Progress)
- PDF resume parsing
- Profile data extraction
- Keyword extraction

### MATCHING Agent (In Progress)
- Claude API integration for job scoring
- Custom question answering
- Application logic

## Safety and Rate Limiting

- Random delays: 30-90 seconds between actions
- Daily limit: Max 25 applications per day (configurable)
- Dry-run mode for testing
- Human-like behavior patterns

## Important Notes

⚠️ **LinkedIn Terms of Service**: This tool automates LinkedIn interactions which may violate their TOS. Use responsibly:
- Personal use only
- Respect rate limits
- Use at your own risk

🔒 **Security**:
- Never commit `.env` file
- API keys stored in environment variables
- Session cookies encrypted at rest

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black src/

# Lint code
ruff check src/

# Type check
mypy src/
```

## Troubleshooting

### "No module named 'job_hunter'"

Make sure you're in the correct directory and have installed the package:
```bash
pip install -e .
```

### "Config file not found"

Run initialization:
```bash
job-hunter init
```

### Playwright browser not installed

Install browsers:
```bash
playwright install chromium
```

## License

MIT License - See LICENSE file for details

## Contributing

This project is under active development by multiple agents working in parallel. Each agent works in their own git worktree:
- `core` - Foundation and CLI (COMPLETED)
- `browser` - LinkedIn automation
- `resume` - Resume parsing
- `matching` - AI-powered matching

## Support

For issues and questions, please open an issue on GitHub.

---

**Version**: 0.1.0
**Status**: Core Foundation Complete ✅
**Last Updated**: 2026-01-06
