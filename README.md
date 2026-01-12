# Job Hunter 🎯

Intelligent LinkedIn Job Application Assistant with AI-powered resume matching.

## Features

- **📄 Resume Parsing**: Upload PDF or JSON resumes with automatic data extraction
- **🔍 Smart Search**: Configure job titles, locations, company sizes, and filters
- **📊 AI Matching**: Get match scores (0-100) with detailed justifications
- **🚀 Easy Apply**: Automated application with rate limiting and safety features

## Quick Start

### Prerequisites

- Python 3.11+
- pip or pipenv

### Installation

```bash
# Clone the repository
git clone https://github.com/Yousefaen/job_hunter.git
cd job_hunter

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run Locally

```bash
# Option 1: Using the run script
python run_ui.py

# Option 2: Direct Streamlit command
streamlit run src/ui/app.py

# With custom port
streamlit run src/ui/app.py --server.port 8080
```

The app will be available at `http://localhost:8501`

## Deployment

### Streamlit Cloud (Recommended)

1. Fork this repository to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub and select this repository
4. Set the main file path to: `src/ui/app.py`
5. Add secrets in the Streamlit Cloud dashboard:
   ```toml
   [linkedin]
   email = "your_email"
   password = "your_password"

   [anthropic]
   api_key = "your_api_key"
   ```

### Heroku

```bash
# Login to Heroku
heroku login

# Create app
heroku create your-job-hunter-app

# Deploy
git push heroku main
```

### Docker

```bash
# Build
docker build -t job-hunter .

# Run
docker run -p 8501:8501 job-hunter
```

## Usage Guide

### 1. Upload Resume

Navigate to the **Resume** page and either:
- Upload a PDF resume
- Upload a JSON profile
- Create a profile manually

### 2. Configure Search

On the **Search** page, set:
- **Job Titles**: Chief of Staff, BizOps, etc.
- **Locations**: Cities or "Remote"
- **Company Size**: Filter by employee count (proxy for startup stage)
- **Exclusions**: Locations or companies to skip

### 3. Review Matches

The **Results** page shows:
- Jobs with match scores (color-coded)
- AI-generated justifications
- Matched skills and concerns
- Select jobs for application

### 4. Apply

On the **Apply** page:
- View application queue
- Set rate limits (default: 25/day)
- Use **Dry Run** mode to test
- Track application history

## Project Structure

```
job_hunter/
├── src/
│   ├── ui/                 # Streamlit web interface
│   │   ├── app.py          # Main app entry
│   │   └── pages/          # Multi-page navigation
│   ├── resume/             # Resume parsing (PDF/JSON)
│   ├── models/             # Data models (Job, Application)
│   ├── agent/              # LinkedIn automation (WIP)
│   └── browser/            # Playwright browser (WIP)
├── data/
│   └── resumes/            # Resume storage
├── config/                 # YAML configurations
├── .streamlit/             # Streamlit config
├── requirements.txt
└── run_ui.py               # Quick start script
```

## Safety & Rate Limiting

- **Daily Limit**: 25 applications per day (configurable)
- **Delays**: 30-90 second random delays between applications
- **Dry Run Mode**: Test without submitting
- **Easy Apply Focus**: Prioritizes LinkedIn Easy Apply jobs

## Tech Stack

| Component | Technology |
|-----------|------------|
| UI | Streamlit |
| Language | Python 3.11+ |
| Resume Parsing | pdfplumber |
| Data Validation | Pydantic |
| Browser Automation | Playwright (WIP) |
| LLM Integration | Anthropic Claude (WIP) |

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add your feature'`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

## License

MIT License - see LICENSE file for details.

## Disclaimer

⚠️ This tool automates LinkedIn interactions which may violate their Terms of Service. Use responsibly:
- Respect rate limits
- Use for personal job searching only
- LinkedIn may restrict automated accounts
