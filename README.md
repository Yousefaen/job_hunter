# Job Hunter - LinkedIn Job Application Agent

An intelligent agent that automates job searching and application on LinkedIn for Chief of Staff / BizOps roles at early-stage startups (Seed to Series A).

## Overview

Job Hunter uses browser automation (Playwright) and AI-powered matching (Claude API) to streamline your job search process. It automatically finds relevant jobs, scores them based on your resume, and submits Easy Apply applications with intelligent question answering.

## Features

- **Resume Upload**: Upload your PDF or JSON resume via CLI
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

## Quick Start

```bash
# 1. Upload your resume
python -m src.main resume upload ~/path/to/your/resume.pdf

# 2. Check status
python -m src.main status

# 3. View configuration
python -m src.main config

# 4. Search for jobs
python -m src.main search

# 5. Apply to jobs
python -m src.main apply --auto
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
target_roles:
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

min_match_score: 60
max_applications_per_day: 25
```

See `config/search_criteria.yaml` for all available options.

## CLI Commands

### Resume Management

```bash
# Upload a resume (PDF or JSON)
python -m src.main resume upload ~/Documents/resume.pdf

# List uploaded resumes
python -m src.main resume list

# Parse and display resume info
python -m src.main resume parse
```

### Job Search & Apply

```bash
# Search LinkedIn and save matching jobs
python -m src.main search

# Apply to all qualified jobs
python -m src.main apply --auto

# Preview applications without submitting
python -m src.main apply --dry-run
```

### Status & Configuration

```bash
# View application statistics
python -m src.main status

# View current configuration
python -m src.main config
```

## Project Structure

```
job_hunter/
├── src/
│   ├── main.py                 # CLI entry point
│   ├── config.py               # Configuration management
│   ├── agent/                  # Agent orchestration
│   │   ├── job_matcher.py      # Claude API job matching
│   │   └── applicant.py        # Easy Apply automation
│   ├── browser/                # Playwright automation
│   │   ├── linkedin_browser.py
│   │   ├── login.py
│   │   └── selectors.py
│   ├── resume/                 # Resume parsing
│   │   ├── parser.py
│   │   └── profile.py
│   ├── models/                 # Data models
│   │   ├── job.py
│   │   ├── application.py
│   │   └── search_criteria.py
│   └── storage/                # Database layer
│       ├── database.py
│       └── schemas.py
├── config/
│   ├── settings.yaml           # Application settings
│   └── search_criteria.yaml    # Job search preferences
├── data/
│   ├── resumes/                # User resume storage
│   └── job_hunter.db           # SQLite database
├── tests/
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Matching Architecture

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

### Score Interpretation

- **80-100**: Excellent match - highly recommended
- **60-79**: Good match - worth applying
- **40-59**: Moderate match - review manually
- **0-39**: Poor match - skip

## Safety & Rate Limiting

Built-in protections:

- **Application Limits**: Max 25 applications/day (configurable)
- **Random Delays**: 30-90 seconds between applications
- **Human-like Behavior**: Typing delays, mouse movements
- **Error Handling**: Graceful failures, detailed logging

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

## Important Notes

⚠️ **LinkedIn Terms of Service**: This tool automates LinkedIn interactions which may violate their TOS. Use responsibly:
- Personal use only
- Respect rate limits
- Use at your own risk

🔒 **Security**:
- Never commit `.env` file
- API keys stored in environment variables
- Session cookies encrypted at rest

## Troubleshooting

### "No module named 'src'"

Make sure you're running from the project root:
```bash
cd job_hunter
python -m src.main --help
```

### Playwright browser not installed

Install browsers:
```bash
playwright install chromium
```

### API key issues

Ensure your `.env` file contains valid credentials:
```bash
ANTHROPIC_API_KEY=sk-ant-...
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=yourpassword
```

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please open an issue on GitHub.

---

**Version**: 0.1.0
