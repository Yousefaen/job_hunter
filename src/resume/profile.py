"""User profile data models."""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class ContactInfo(BaseModel):
    """Contact information for the user."""

    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    location: Optional[str] = Field(None, description="Current location (city, state)")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    website: Optional[str] = Field(None, description="Personal website or portfolio")


class WorkExperience(BaseModel):
    """Work experience entry."""

    company: str = Field(..., description="Company name")
    title: str = Field(..., description="Job title")
    location: Optional[str] = Field(None, description="Job location")
    start_date: Optional[str] = Field(None, description="Start date (flexible format)")
    end_date: Optional[str] = Field(None, description="End date or 'Present'")
    description: Optional[str] = Field(None, description="Role description")
    achievements: list[str] = Field(
        default_factory=list, description="Key achievements and responsibilities"
    )

    @property
    def is_current(self) -> bool:
        """Check if this is a current position."""
        if not self.end_date:
            return False
        return self.end_date.lower() in ["present", "current", "now"]

    @property
    def duration_text(self) -> str:
        """Get formatted duration text."""
        if not self.start_date:
            return ""
        end = self.end_date or "Present"
        return f"{self.start_date} - {end}"


class Education(BaseModel):
    """Education entry."""

    institution: str = Field(..., description="School/University name")
    degree: Optional[str] = Field(None, description="Degree type (BS, MS, PhD, etc.)")
    field: Optional[str] = Field(None, description="Field of study/major")
    graduation_date: Optional[str] = Field(None, description="Graduation date")
    gpa: Optional[str] = Field(None, description="GPA if notable")
    honors: list[str] = Field(default_factory=list, description="Honors and awards")


class UserProfile(BaseModel):
    """Complete user profile parsed from resume."""

    contact: ContactInfo = Field(..., description="Contact information")
    summary: Optional[str] = Field(None, description="Professional summary/objective")
    skills: list[str] = Field(default_factory=list, description="Technical and soft skills")
    work_experience: list[WorkExperience] = Field(
        default_factory=list, description="Work history"
    )
    education: list[Education] = Field(default_factory=list, description="Education history")
    certifications: list[str] = Field(
        default_factory=list, description="Professional certifications"
    )
    languages: list[str] = Field(default_factory=list, description="Languages spoken")

    def get_keywords(self) -> list[str]:
        """Extract keywords for job matching.

        Returns:
            List of unique keywords from skills, job titles, and key terms.
        """
        keywords = set()

        # Add skills
        for skill in self.skills:
            keywords.add(skill.lower())

        # Add job titles
        for exp in self.work_experience:
            keywords.add(exp.title.lower())
            # Extract key words from titles
            title_words = exp.title.lower().split()
            keywords.update(word for word in title_words if len(word) > 3)

        # Add education fields
        for edu in self.education:
            if edu.field:
                keywords.add(edu.field.lower())
            if edu.degree:
                keywords.add(edu.degree.lower())

        # Add certifications
        for cert in self.certifications:
            keywords.add(cert.lower())

        return sorted(list(keywords))

    def get_current_title(self) -> Optional[str]:
        """Get the most recent or current job title.

        Returns:
            Current job title or None.
        """
        for exp in self.work_experience:
            if exp.is_current:
                return exp.title

        # Return first experience if no current role
        if self.work_experience:
            return self.work_experience[0].title

        return None

    def get_job_count(self) -> int:
        """Get the number of work experience entries.

        Returns:
            Number of jobs listed in work experience.
        """
        return len(self.work_experience)

    def has_skill(self, skill: str) -> bool:
        """Check if profile contains a specific skill.

        Args:
            skill: Skill to search for (case-insensitive).

        Returns:
            True if skill is found.
        """
        skill_lower = skill.lower()
        return any(skill_lower in s.lower() for s in self.skills)

    def to_text_summary(self) -> str:
        """Generate a text summary of the profile for LLM consumption.

        Returns:
            Formatted text summary of the profile.
        """
        parts = []

        # Contact
        parts.append(f"Name: {self.contact.name}")
        if self.contact.location:
            parts.append(f"Location: {self.contact.location}")

        # Summary
        if self.summary:
            parts.append(f"\nSummary:\n{self.summary}")

        # Experience
        if self.work_experience:
            parts.append("\nWork Experience:")
            for exp in self.work_experience:
                parts.append(f"\n- {exp.title} at {exp.company}")
                if exp.duration_text:
                    parts.append(f"  {exp.duration_text}")
                if exp.description:
                    parts.append(f"  {exp.description}")
                for achievement in exp.achievements[:3]:  # Top 3 achievements
                    parts.append(f"  • {achievement}")

        # Education
        if self.education:
            parts.append("\nEducation:")
            for edu in self.education:
                edu_line = f"- {edu.institution}"
                if edu.degree and edu.field:
                    edu_line += f" - {edu.degree} in {edu.field}"
                elif edu.degree:
                    edu_line += f" - {edu.degree}"
                parts.append(edu_line)

        # Skills
        if self.skills:
            parts.append(f"\nSkills:\n{', '.join(self.skills)}")

        # Certifications
        if self.certifications:
            parts.append(f"\nCertifications:\n{', '.join(self.certifications)}")

        return "\n".join(parts)
