"""Tests for resume parsing and profile management."""

import json
import pytest
from pathlib import Path
from pydantic import ValidationError

from src.resume.parser import ResumeParser
from src.resume.profile import (
    UserProfile,
    ContactInfo,
    WorkExperience,
    Education,
)


class TestContactInfo:
    """Tests for ContactInfo model."""

    def test_contact_info_creation(self):
        """Test creating a ContactInfo object."""
        contact = ContactInfo(
            name="John Doe",
            email="john@example.com",
            phone="+1 555-1234",
            location="New York, NY",
        )

        assert contact.name == "John Doe"
        assert contact.email == "john@example.com"
        assert contact.phone == "+1 555-1234"
        assert contact.location == "New York, NY"

    def test_contact_info_email_validation(self):
        """Test email validation."""
        with pytest.raises(ValidationError):
            ContactInfo(name="John Doe", email="invalid-email")


class TestWorkExperience:
    """Tests for WorkExperience model."""

    def test_work_experience_creation(self):
        """Test creating a WorkExperience object."""
        exp = WorkExperience(
            company="TechCorp",
            title="Software Engineer",
            start_date="Jan 2020",
            end_date="Present",
            description="Building awesome software",
            achievements=["Led team of 5", "Shipped product v2.0"],
        )

        assert exp.company == "TechCorp"
        assert exp.title == "Software Engineer"
        assert exp.is_current is True

    def test_is_current_property(self):
        """Test is_current property."""
        current_exp = WorkExperience(
            company="Company A", title="Engineer", end_date="Present"
        )
        past_exp = WorkExperience(
            company="Company B", title="Engineer", end_date="Dec 2020"
        )

        assert current_exp.is_current is True
        assert past_exp.is_current is False

    def test_duration_text_property(self):
        """Test duration_text property."""
        exp = WorkExperience(
            company="Company",
            title="Engineer",
            start_date="Jan 2020",
            end_date="Dec 2022",
        )

        assert exp.duration_text == "Jan 2020 - Dec 2022"


class TestEducation:
    """Tests for Education model."""

    def test_education_creation(self):
        """Test creating an Education object."""
        edu = Education(
            institution="MIT",
            degree="Bachelor of Science",
            field="Computer Science",
            graduation_date="2020",
            honors=["Summa Cum Laude"],
        )

        assert edu.institution == "MIT"
        assert edu.degree == "Bachelor of Science"
        assert edu.field == "Computer Science"
        assert len(edu.honors) == 1


class TestUserProfile:
    """Tests for UserProfile model."""

    @pytest.fixture
    def sample_profile(self):
        """Create a sample user profile for testing."""
        contact = ContactInfo(
            name="Jane Smith",
            email="jane@example.com",
            location="San Francisco, CA",
        )

        experience = [
            WorkExperience(
                company="StartupCo",
                title="Chief of Staff",
                start_date="Jan 2021",
                end_date="Present",
                achievements=["Led strategic initiatives", "Managed OKR process"],
            ),
            WorkExperience(
                company="BigCorp",
                title="Business Operations Manager",
                start_date="Jun 2018",
                end_date="Dec 2020",
            ),
        ]

        education = [
            Education(
                institution="Stanford University",
                degree="BS",
                field="Economics",
                graduation_date="2018",
            )
        ]

        return UserProfile(
            contact=contact,
            summary="Experienced Chief of Staff",
            skills=["Strategic Planning", "Data Analysis", "Python", "SQL"],
            work_experience=experience,
            education=education,
            certifications=["PMP"],
        )

    def test_profile_creation(self, sample_profile):
        """Test creating a UserProfile object."""
        assert sample_profile.contact.name == "Jane Smith"
        assert len(sample_profile.work_experience) == 2
        assert len(sample_profile.education) == 1

    def test_get_keywords(self, sample_profile):
        """Test keyword extraction."""
        keywords = sample_profile.get_keywords()

        assert "strategic planning" in keywords
        assert "python" in keywords
        assert "chief of staff" in keywords
        assert "economics" in keywords
        assert "pmp" in keywords

    def test_get_current_title(self, sample_profile):
        """Test getting current job title."""
        title = sample_profile.get_current_title()
        assert title == "Chief of Staff"

    def test_has_skill(self, sample_profile):
        """Test skill checking."""
        assert sample_profile.has_skill("Python") is True
        assert sample_profile.has_skill("python") is True
        assert sample_profile.has_skill("Java") is False

    def test_to_text_summary(self, sample_profile):
        """Test text summary generation."""
        summary = sample_profile.to_text_summary()

        assert "Jane Smith" in summary
        assert "Chief of Staff" in summary
        assert "Strategic Planning" in summary
        assert "Stanford University" in summary


class TestResumeParser:
    """Tests for ResumeParser."""

    @pytest.fixture
    def parser(self):
        """Create a ResumeParser instance."""
        return ResumeParser()

    @pytest.fixture
    def sample_json_profile(self, tmp_path):
        """Create a sample JSON profile file."""
        profile_data = {
            "contact": {
                "name": "Test User",
                "email": "test@example.com",
                "phone": "555-1234",
                "location": "Boston, MA",
            },
            "summary": "Experienced professional",
            "skills": ["Python", "Project Management"],
            "work_experience": [
                {
                    "company": "TestCorp",
                    "title": "Manager",
                    "start_date": "2020",
                    "end_date": "Present",
                    "achievements": ["Led team"],
                }
            ],
            "education": [
                {
                    "institution": "Harvard",
                    "degree": "MBA",
                    "field": "Business",
                    "graduation_date": "2019",
                }
            ],
            "certifications": ["PMP"],
            "languages": ["English"],
        }

        json_file = tmp_path / "profile.json"
        with open(json_file, "w") as f:
            json.dump(profile_data, f)

        return json_file

    def test_parse_json(self, parser, sample_json_profile):
        """Test parsing JSON profile."""
        profile = parser.parse_json(sample_json_profile)

        assert profile.contact.name == "Test User"
        assert profile.contact.email == "test@example.com"
        assert len(profile.skills) == 2
        assert len(profile.work_experience) == 1
        assert profile.work_experience[0].company == "TestCorp"

    def test_parse_file_json(self, parser, sample_json_profile):
        """Test parse_file with JSON."""
        profile = parser.parse_file(sample_json_profile)

        assert isinstance(profile, UserProfile)
        assert profile.contact.name == "Test User"

    def test_parse_file_not_found(self, parser):
        """Test parse_file with non-existent file."""
        with pytest.raises(FileNotFoundError):
            parser.parse_file("nonexistent.pdf")

    def test_parse_file_unsupported_format(self, parser, tmp_path):
        """Test parse_file with unsupported format."""
        bad_file = tmp_path / "resume.txt"
        bad_file.write_text("Some text")

        with pytest.raises(ValueError, match="Unsupported file format"):
            parser.parse_file(bad_file)

    def test_extract_contact_info(self, parser):
        """Test extracting contact info from text."""
        lines = [
            "John Doe",
            "john.doe@example.com | +1 (555) 123-4567",
            "New York, NY",
            "linkedin.com/in/johndoe",
        ]

        contact = parser._extract_contact_info(lines)

        assert contact.name == "John Doe"
        assert contact.email == "john.doe@example.com"
        assert contact.phone is not None
        assert contact.location == "New York, NY"
        assert "linkedin.com" in (contact.linkedin_url or "")

    def test_extract_skills(self, parser):
        """Test extracting skills from text."""
        text = "• Python\n• JavaScript\n• Project Management\n• Data Analysis"
        skills = parser._extract_skills(text)

        assert len(skills) == 4
        assert "Python" in skills
        assert "JavaScript" in skills

    def test_extract_skills_comma_separated(self, parser):
        """Test extracting comma-separated skills."""
        text = "Python, JavaScript, SQL, Excel, Tableau"
        skills = parser._extract_skills(text)

        assert len(skills) == 5
        assert "Python" in skills

    def test_split_into_sections(self, parser):
        """Test splitting resume into sections."""
        text = """
John Doe
john@example.com

SUMMARY
Experienced professional with strong background

EXPERIENCE
Chief of Staff at StartupCo
Led strategic initiatives

EDUCATION
MIT - Bachelor of Science

SKILLS
Python, SQL, Leadership
"""
        sections = parser._split_into_sections(text)

        assert "summary" in sections
        assert "experience" in sections
        assert "education" in sections
        assert "skills" in sections
        assert "Experienced professional" in sections["summary"]

    def test_parse_experience_header_with_at(self, parser):
        """Test parsing experience header with 'at' format."""
        line = "Chief of Staff at TechCorp | Jan 2020 - Present"
        exp = parser._parse_experience_header(line)

        assert exp.title == "Chief of Staff"
        assert exp.company == "TechCorp"
        assert exp.start_date == "Jan 2020"
        assert exp.end_date == "Present"

    def test_parse_experience_header_with_pipe(self, parser):
        """Test parsing experience header with pipe separator."""
        line = "Software Engineer | Google | 2019 - 2021"
        exp = parser._parse_experience_header(line)

        assert "Software Engineer" in exp.title or "Google" in exp.company

    def test_parse_education_line(self, parser):
        """Test parsing education line."""
        line = "Massachusetts Institute of Technology - BS in Computer Science, 2020"
        edu = parser._parse_education_line(line)

        assert "Massachusetts Institute" in edu.institution
        assert edu.degree is not None
        assert edu.graduation_date == "2020"

    def test_extract_certifications(self, parser):
        """Test extracting certifications."""
        text = "• PMP Certification\n• AWS Solutions Architect\n• Six Sigma Green Belt"
        certs = parser._extract_certifications(text)

        assert len(certs) == 3
        assert "PMP Certification" in certs


class TestIntegration:
    """Integration tests for resume parsing."""

    def test_full_json_parsing_workflow(self, tmp_path):
        """Test complete workflow of parsing a JSON profile."""
        # Use the template as a test case
        template_path = Path("data/resumes/profile_template.json")

        if template_path.exists():
            parser = ResumeParser()
            profile = parser.parse_json(template_path)

            # Verify profile is complete
            assert profile.contact.name == "John Doe"
            assert len(profile.skills) > 0
            assert len(profile.work_experience) > 0
            assert len(profile.education) > 0

            # Test keyword extraction
            keywords = profile.get_keywords()
            assert len(keywords) > 0

            # Test text summary
            summary = profile.to_text_summary()
            assert "John Doe" in summary
