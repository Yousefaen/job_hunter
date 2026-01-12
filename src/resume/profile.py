"""User profile and resume data models."""

from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ContactInfo(BaseModel):
    """Contact information for a user."""

    name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    website: Optional[str] = None


class WorkExperience(BaseModel):
    """Work experience entry."""

    company: str
    title: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    achievements: list[str] = Field(default_factory=list)

    @property
    def is_current(self) -> bool:
        """Check if this is current position."""
        if not self.end_date:
            return True
        return str(self.end_date).lower() in ["present", "current", "now"]

    @property
    def duration_text(self) -> str:
        """Get formatted duration text."""
        if self.start_date and self.end_date:
            return f"{self.start_date} - {self.end_date}"
        elif self.start_date:
            return f"{self.start_date} - Present"
        return ""


class Education(BaseModel):
    """Education entry."""

    institution: str
    degree: Optional[str] = None
    field: Optional[str] = None
    graduation_date: Optional[str] = None
    gpa: Optional[str] = None
    honors: list[str] = Field(default_factory=list)


class UserProfile(BaseModel):
    """User profile containing resume information."""

    # Contact information
    contact: ContactInfo

    # Profile summary
    summary: Optional[str] = None

    # Skills
    skills: list[str] = Field(default_factory=list)

    # Work experience
    work_experience: list[WorkExperience] = Field(default_factory=list)

    # Education
    education: list[Education] = Field(default_factory=list)

    # Certifications
    certifications: list[str] = Field(default_factory=list)

    # Languages
    languages: list[str] = Field(default_factory=list)

    def get_keywords(self) -> list[str]:
        """Extract keywords from profile for matching.

        Returns:
            List of keywords including skills, job titles, and key terms
        """
        keywords = []

        # Add skills
        keywords.extend(skill.lower() for skill in self.skills)

        # Add job titles and companies
        for exp in self.work_experience:
            keywords.append(exp.title.lower())
            keywords.append(exp.company.lower())

        # Add education fields
        for edu in self.education:
            if edu.field:
                keywords.append(edu.field.lower())
            if edu.degree:
                keywords.append(edu.degree.lower())

        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique.append(kw)

        return unique

    def get_current_title(self) -> Optional[str]:
        """Get current or most recent job title."""
        for exp in self.work_experience:
            if exp.is_current:
                return exp.title
        if self.work_experience:
            return self.work_experience[0].title
        return None

    def get_job_count(self) -> int:
        """Get number of jobs in work history."""
        return len(self.work_experience)

    def has_skill(self, skill: str) -> bool:
        """Check if profile has a specific skill."""
        skill_lower = skill.lower()
        return any(skill_lower in s.lower() for s in self.skills)

    def to_text_summary(self) -> str:
        """Get a text summary of the profile for LLM prompts.

        Returns:
            Formatted text summary
        """
        parts = []

        # Header
        parts.append(f"Name: {self.contact.name}")
        if self.contact.location:
            parts.append(f"Location: {self.contact.location}")

        # Summary
        if self.summary:
            parts.append(f"\nSUMMARY:\n{self.summary}")

        # Skills
        if self.skills:
            parts.append(f"\nSKILLS:\n{', '.join(self.skills)}")

        # Experience
        if self.work_experience:
            parts.append("\nEXPERIENCE:")
            for exp in self.work_experience:
                parts.append(f"\n{exp.title} at {exp.company}")
                if exp.duration_text:
                    parts.append(f"  {exp.duration_text}")
                if exp.description:
                    parts.append(f"  {exp.description}")
                if exp.achievements:
                    for achievement in exp.achievements:
                        parts.append(f"  - {achievement}")

        # Education
        if self.education:
            parts.append("\nEDUCATION:")
            for edu in self.education:
                degree_info = edu.degree or "Degree"
                if edu.field:
                    degree_info += f" in {edu.field}"
                parts.append(f"\n{degree_info} - {edu.institution}")
                if edu.graduation_date:
                    parts.append(f"  Graduated: {edu.graduation_date}")

        return "\n".join(parts)

    # Alias for compatibility
    def get_summary_text(self) -> str:
        """Alias for to_text_summary for compatibility."""
        return self.to_text_summary()

    model_config = ConfigDict(
        ser_json_timedelta="iso8601",
    )
