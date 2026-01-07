"""User profile and resume data models."""

from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Experience(BaseModel):
    """Work experience entry."""

    company: str
    title: str
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    current: bool = False
    description: str = ""
    achievements: list[str] = Field(default_factory=list)


class Education(BaseModel):
    """Education entry."""

    institution: str
    degree: str
    field_of_study: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    gpa: Optional[str] = None
    achievements: list[str] = Field(default_factory=list)


class UserProfile(BaseModel):
    """User profile containing resume information."""

    # Contact information
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None

    # Profile summary
    summary: str = ""
    headline: Optional[str] = None

    # Skills
    skills: list[str] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)

    # Experience
    experiences: list[Experience] = Field(default_factory=list)

    # Education
    education: list[Education] = Field(default_factory=list)

    # Certifications
    certifications: list[str] = Field(default_factory=list)

    # Languages
    languages: list[str] = Field(default_factory=list)

    def get_keywords(self) -> set[str]:
        """Extract keywords from profile for matching.

        Returns:
            Set of keywords including skills, job titles, and key terms
        """
        keywords = set()

        # Add skills
        keywords.update(skill.lower() for skill in self.skills)
        keywords.update(skill.lower() for skill in self.technical_skills)

        # Add job titles
        for exp in self.experiences:
            keywords.add(exp.title.lower())
            keywords.add(exp.company.lower())

        # Add education fields
        for edu in self.education:
            if edu.field_of_study:
                keywords.add(edu.field_of_study.lower())

        return keywords

    def get_total_years_experience(self) -> float:
        """Calculate total years of work experience.

        Returns:
            Total years of experience
        """
        total_days = 0
        for exp in self.experiences:
            if exp.start_date:
                end = exp.end_date or date.today()
                days = (end - exp.start_date).days
                total_days += days

        return total_days / 365.25

    def get_summary_text(self) -> str:
        """Get a text summary of the profile for LLM prompts.

        Returns:
            Formatted text summary
        """
        parts = []

        # Header
        if self.headline:
            parts.append(f"{self.full_name} - {self.headline}")
        else:
            parts.append(self.full_name)

        if self.location:
            parts.append(f"Location: {self.location}")

        # Summary
        if self.summary:
            parts.append(f"\nSUMMARY:\n{self.summary}")

        # Skills
        if self.skills or self.technical_skills:
            all_skills = self.skills + self.technical_skills
            parts.append(f"\nSKILLS:\n{', '.join(all_skills)}")

        # Experience
        if self.experiences:
            parts.append("\nEXPERIENCE:")
            for exp in self.experiences:
                date_range = ""
                if exp.start_date:
                    start = exp.start_date.strftime("%b %Y")
                    end = "Present" if exp.current else (
                        exp.end_date.strftime("%b %Y") if exp.end_date else ""
                    )
                    date_range = f" ({start} - {end})"

                parts.append(f"\n{exp.title} at {exp.company}{date_range}")
                if exp.description:
                    parts.append(exp.description)
                if exp.achievements:
                    parts.append("Achievements:")
                    for achievement in exp.achievements:
                        parts.append(f"  - {achievement}")

        # Education
        if self.education:
            parts.append("\nEDUCATION:")
            for edu in self.education:
                degree_info = f"{edu.degree}"
                if edu.field_of_study:
                    degree_info += f" in {edu.field_of_study}"
                parts.append(f"\n{degree_info} - {edu.institution}")

        return "\n".join(parts)

    model_config = ConfigDict(
        ser_json_timedelta="iso8601",
    )
