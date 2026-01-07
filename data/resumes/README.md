# Resume Storage

This directory stores your resume files for the LinkedIn job application agent.

## Supported Formats

### 1. PDF Resume (Recommended for existing resumes)
- Place your PDF resume in this directory
- The parser will automatically extract contact info, skills, experience, and education
- Works best with standard resume formats

### 2. JSON Profile (Recommended for best accuracy)
- Use `profile_template.json` as a starting point
- Fill in your information following the structure
- This format ensures 100% parsing accuracy
- JSON profiles can be validated and edited easily

## Usage

### Using a PDF Resume
```bash
# The agent will automatically parse your PDF
python -m src.main --resume data/resumes/my_resume.pdf
```

### Using a JSON Profile
```bash
# Create your profile from the template
cp data/resumes/profile_template.json data/resumes/my_profile.json
# Edit my_profile.json with your information
# Then use it with the agent
python -m src.main --resume data/resumes/my_profile.json
```

## JSON Profile Structure

The JSON profile has the following sections:

- **contact**: Your contact information (name, email, phone, location, LinkedIn, website)
- **summary**: Professional summary or objective statement
- **skills**: List of technical and soft skills
- **work_experience**: Array of work history entries with achievements
- **education**: Array of educational background
- **certifications**: List of professional certifications
- **languages**: Languages you speak

## Tips for Best Results

### For PDF Resumes:
- Use clear section headers (Experience, Education, Skills, etc.)
- Use standard date formats (Jan 2020 - Present, 2018-2020, etc.)
- Keep formatting simple and clean
- Include contact info at the top

### For JSON Profiles:
- Fill in all relevant fields
- Use complete sentences for achievements
- List skills from most to least relevant
- Include quantifiable achievements when possible
- Keep dates in consistent format (e.g., "Jan 2020" or "2020")

## Privacy & Security

- Never commit your actual resume files to version control
- This directory is included in `.gitignore`
- Your resume data is stored locally only
- Only you have access to these files
