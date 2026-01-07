# Resume Parser Module

This module handles parsing resumes from PDF and JSON formats into structured `UserProfile` objects.

## Features

- **PDF Parsing**: Extract structured data from PDF resumes using heuristic-based text analysis
- **JSON Profiles**: Load pre-structured profiles from JSON files for 100% accuracy
- **Flexible Extraction**: Handles various resume formats and layouts
- **Keyword Extraction**: Automatically extract skills and keywords for job matching
- **Validation**: Pydantic-based data validation ensures data quality

## Usage

### Basic Usage

```python
from src.resume.parser import ResumeParser

# Initialize parser
parser = ResumeParser()

# Parse PDF resume
profile = parser.parse_file("data/resumes/my_resume.pdf")

# Or parse JSON profile
profile = parser.parse_file("data/resumes/my_profile.json")

# Access profile data
print(f"Name: {profile.contact.name}")
print(f"Current Title: {profile.get_current_title()}")
print(f"Skills: {', '.join(profile.skills)}")
```

### Working with UserProfile

```python
# Get keywords for job matching
keywords = profile.get_keywords()
print(f"Keywords: {keywords}")

# Check for specific skills
if profile.has_skill("Python"):
    print("Has Python experience")

# Get text summary for LLM consumption
summary = profile.to_text_summary()
print(summary)

# Access work experience
for exp in profile.work_experience:
    print(f"{exp.title} at {exp.company}")
    print(f"Duration: {exp.duration_text}")
    if exp.is_current:
        print("(Current Position)")
```

## Data Models

### UserProfile
Main profile object containing all resume information.

**Fields:**
- `contact`: ContactInfo - contact information
- `summary`: Optional[str] - professional summary
- `skills`: list[str] - technical and soft skills
- `work_experience`: list[WorkExperience] - work history
- `education`: list[Education] - educational background
- `certifications`: list[str] - professional certifications
- `languages`: list[str] - languages spoken

**Methods:**
- `get_keywords()` - Extract keywords for matching
- `get_current_title()` - Get current or most recent job title
- `has_skill(skill)` - Check if profile has a specific skill
- `to_text_summary()` - Generate text summary for LLMs

### ContactInfo
Contact information fields.

**Fields:**
- `name`: str - full name (required)
- `email`: EmailStr - email address (required)
- `phone`: Optional[str] - phone number
- `location`: Optional[str] - current location
- `linkedin_url`: Optional[str] - LinkedIn profile URL
- `website`: Optional[str] - personal website

### WorkExperience
Individual work experience entry.

**Fields:**
- `company`: str - company name
- `title`: str - job title
- `location`: Optional[str] - job location
- `start_date`: Optional[str] - start date
- `end_date`: Optional[str] - end date or "Present"
- `description`: Optional[str] - role description
- `achievements`: list[str] - key achievements

**Properties:**
- `is_current`: bool - whether this is a current position
- `duration_text`: str - formatted duration string

### Education
Educational background entry.

**Fields:**
- `institution`: str - school/university name
- `degree`: Optional[str] - degree type
- `field`: Optional[str] - field of study
- `graduation_date`: Optional[str] - graduation date
- `gpa`: Optional[str] - GPA if notable
- `honors`: list[str] - honors and awards

## JSON Profile Format

See `data/resumes/profile_template.json` for a complete example.

```json
{
  "contact": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1 555-1234",
    "location": "New York, NY"
  },
  "summary": "Professional summary...",
  "skills": ["Python", "SQL", "Leadership"],
  "work_experience": [...],
  "education": [...],
  "certifications": [...],
  "languages": [...]
}
```

## PDF Parsing

The PDF parser uses heuristic-based text extraction:

1. **Text Extraction**: Uses `pdfplumber` to extract text from all pages
2. **Section Detection**: Identifies sections (Experience, Education, Skills) by headers
3. **Contact Extraction**: Uses regex patterns to find email, phone, location
4. **Date Parsing**: Extracts dates in various formats
5. **Structured Output**: Organizes extracted data into Pydantic models

### Supported Resume Formats

The parser works best with:
- Clear section headers (EXPERIENCE, EDUCATION, SKILLS, etc.)
- Standard date formats (Jan 2020, 2018-2020, Jan 2020 - Present)
- Bullet points or clear line breaks for lists
- Contact information at the top

### Limitations

- Complex multi-column layouts may not parse correctly
- Heavy formatting or graphics can interfere with text extraction
- Non-standard section names may not be recognized
- Date parsing may fail for unusual formats

**Tip**: For best results, use the JSON profile format or ensure your PDF resume follows standard formatting conventions.

## Testing

Run tests with:

```bash
pytest tests/test_resume.py -v
```

Test coverage includes:
- Data model validation
- JSON parsing
- Contact info extraction
- Skills parsing
- Work experience parsing
- Education parsing
- Keyword extraction
- Text summary generation

## Integration Points

This module integrates with:

- **Job Matcher**: Uses `UserProfile.to_text_summary()` and keywords for LLM-based matching
- **Application Engine**: Uses profile data to fill Easy Apply forms
- **Database**: Profile data is stored in SQLite for tracking

## Error Handling

The parser handles various error cases:
- Missing or corrupted PDF files
- Invalid JSON structure
- Missing required fields (falls back to defaults)
- Unrecognized resume sections (graceful degradation)

Example:
```python
try:
    profile = parser.parse_file("resume.pdf")
except FileNotFoundError:
    print("Resume file not found")
except ValueError as e:
    print(f"Parsing error: {e}")
```

## Best Practices

1. **Prefer JSON for accuracy**: If starting fresh, use JSON profile format
2. **Validate after parsing**: Check that critical fields were extracted
3. **Test with your resume**: Run parser on your actual resume to verify
4. **Keep skills updated**: Manually review and add skills if needed
5. **Use descriptive achievements**: Include quantifiable results in work experience
