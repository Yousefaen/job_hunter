"""Resume parsing from PDF and JSON formats."""

import json
import re
from pathlib import Path
from typing import Optional, Any

import pdfplumber

from .profile import (
    UserProfile,
    ContactInfo,
    WorkExperience,
    Education,
)


class ResumeParser:
    """Parser for extracting structured data from resumes."""

    # Common section headers to look for
    # Patterns use ^ and $ anchors to match only standalone section headers
    SECTION_PATTERNS = {
        "experience": r"^(work\s+experience|experience|employment|professional\s+experience)\s*:?\s*$",
        "education": r"^(education|academic|degrees?)\s*:?\s*$",
        "skills": r"^(skills?|technical\s+skills?|core\s+competencies)\s*:?\s*$",
        "summary": r"^(summary|objective|profile|about)\s*:?\s*$",
        "certifications": r"^(certifications?|licenses?)\s*:?\s*$",
    }

    def __init__(self):
        """Initialize the resume parser."""
        pass

    def parse_file(self, file_path: str | Path) -> UserProfile:
        """Parse a resume file (PDF or JSON).

        Args:
            file_path: Path to resume file.

        Returns:
            Parsed UserProfile.

        Raises:
            ValueError: If file format is unsupported.
            FileNotFoundError: If file doesn't exist.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Resume file not found: {file_path}")

        if file_path.suffix.lower() == ".pdf":
            return self.parse_pdf(file_path)
        elif file_path.suffix.lower() == ".json":
            return self.parse_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

    def parse_json(self, file_path: str | Path) -> UserProfile:
        """Parse a JSON profile file.

        Args:
            file_path: Path to JSON file.

        Returns:
            Parsed UserProfile.

        Raises:
            ValueError: If JSON is malformed or validation fails.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}") from e

        try:
            return UserProfile(**data)
        except Exception as e:
            raise ValueError(f"Invalid profile data in {file_path}: {e}") from e

    def parse_pdf(self, file_path: str | Path) -> UserProfile:
        """Parse a PDF resume.

        Args:
            file_path: Path to PDF file.

        Returns:
            Parsed UserProfile.
        """
        text = self._extract_pdf_text(file_path)
        return self._parse_text(text)

    def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from PDF file.

        Args:
            file_path: Path to PDF file.

        Returns:
            Extracted text.

        Raises:
            ValueError: If no text could be extracted from the PDF.
        """
        text_parts = []

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        if not text_parts:
            raise ValueError(
                f"Could not extract text from {file_path}. "
                "The PDF may be image-based (requires OCR), empty, or corrupted. "
                "Please try using the JSON profile format instead."
            )

        return "\n".join(text_parts)

    def _parse_text(self, text: str) -> UserProfile:
        """Parse resume text into structured profile.

        Args:
            text: Resume text content.

        Returns:
            Parsed UserProfile.
        """
        # Split text into lines
        lines = text.split("\n")

        # Extract contact info (usually at the top)
        contact = self._extract_contact_info(lines[:10])

        # Find sections
        sections = self._split_into_sections(text)

        # Parse each section
        summary = self._extract_summary(sections.get("summary", ""))
        skills = self._extract_skills(sections.get("skills", ""))
        work_experience = self._extract_work_experience(sections.get("experience", ""))
        education = self._extract_education(sections.get("education", ""))
        certifications = self._extract_certifications(sections.get("certifications", ""))

        return UserProfile(
            contact=contact,
            summary=summary,
            skills=skills,
            work_experience=work_experience,
            education=education,
            certifications=certifications,
        )

    def _extract_contact_info(self, lines: list[str]) -> ContactInfo:
        """Extract contact information from header lines.

        Args:
            lines: First few lines of resume.

        Returns:
            ContactInfo object.
        """
        text = " ".join(lines)

        # Extract name (usually first non-empty line)
        name = lines[0].strip() if lines else "Unknown"

        # Extract email (more robust pattern)
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        email_match = re.search(email_pattern, text)
        if not email_match:
            raise ValueError(
                "Could not extract email address from resume. "
                "Please ensure your resume includes a valid email address, "
                "or use the JSON profile format for manual entry."
            )
        email = email_match.group(0)

        # Extract phone (safer pattern to avoid ReDoS)
        phone_pattern = r"(?:\+?1[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]?\d{3}[\s.-]?\d{4}"
        phone_match = re.search(phone_pattern, text)
        phone = phone_match.group(0) if phone_match else None

        # Extract location (common patterns: City, State or City, ST)
        location_pattern = r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*([A-Z]{2}|[A-Z][a-z]+)"
        location_match = re.search(location_pattern, text)
        location = location_match.group(0) if location_match else None

        # Extract LinkedIn URL
        linkedin_pattern = r"linkedin\.com/in/[\w-]+"
        linkedin_match = re.search(linkedin_pattern, text)
        linkedin_url = f"https://{linkedin_match.group(0)}" if linkedin_match else None

        return ContactInfo(
            name=name,
            email=email,
            phone=phone,
            location=location,
            linkedin_url=linkedin_url,
        )

    def _split_into_sections(self, text: str) -> dict[str, str]:
        """Split resume text into sections.

        Args:
            text: Full resume text.

        Returns:
            Dictionary mapping section names to their content.
        """
        sections = {}
        current_section = None
        current_content = []

        lines = text.split("\n")

        for line in lines:
            # Check if line is a section header
            line_lower = line.lower().strip()
            matched_section = None

            for section_name, pattern in self.SECTION_PATTERNS.items():
                if re.match(pattern, line_lower):
                    matched_section = section_name
                    break

            if matched_section:
                # Save previous section
                if current_section:
                    sections[current_section] = "\n".join(current_content)

                # Start new section
                current_section = matched_section
                current_content = []
            elif current_section:
                # Add line to current section
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = "\n".join(current_content)

        return sections

    def _extract_summary(self, text: str) -> Optional[str]:
        """Extract professional summary.

        Args:
            text: Summary section text.

        Returns:
            Summary text or None.
        """
        text = text.strip()
        return text if text else None

    def _extract_skills(self, text: str) -> list[str]:
        """Extract skills from skills section.

        Args:
            text: Skills section text.

        Returns:
            List of skills.
        """
        if not text:
            return []

        skills = []

        # Split by common delimiters
        # Try bullet points first - check each line for bullets
        lines = text.split("\n")
        has_bullets = any(line.strip().startswith(("•", "-", "*")) for line in lines)

        if has_bullets:
            for line in lines:
                # Remove bullet points and trim
                skill = re.sub(r"^[\s•\-\*]+", "", line).strip()
                if skill and len(skill) > 1:
                    skills.append(skill)
        else:
            # Try comma-separated or semicolon-separated
            separators = [",", ";", "|"]
            for sep in separators:
                if sep in text:
                    parts = text.split(sep)
                    skills = [s.strip() for s in parts if s.strip()]
                    break

        # If still no skills, split by lines
        if not skills:
            skills = [line.strip() for line in text.split("\n") if line.strip()]

        return skills

    def _extract_work_experience(self, text: str) -> list[WorkExperience]:
        """Extract work experience entries.

        Args:
            text: Experience section text.

        Returns:
            List of WorkExperience objects.
        """
        if not text:
            return []

        experiences = []
        lines = text.split("\n")

        # Simple heuristic: look for company/title patterns
        # Pattern: Company Name | Job Title | Dates
        # or: Job Title at Company Name | Dates

        current_exp = None
        current_achievements = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if it's a job header (usually has dates)
            date_pattern = r"\d{4}|\d{1,2}/\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}"
            has_date = re.search(date_pattern, line)

            # Check for common title/company indicators
            is_header = (
                has_date
                or "|" in line
                or " at " in line.lower()
                or (re.match(r"^[A-Z]", line) and len(line) < 100)
            )

            if is_header and (has_date or "|" in line or " at " in line.lower()):
                # Save previous experience
                if current_exp:
                    current_exp.achievements = current_achievements
                    experiences.append(current_exp)

                # Parse new experience header
                current_exp = self._parse_experience_header(line)
                current_achievements = []

            elif current_exp and line:
                # This is an achievement/description line
                # Remove bullet points
                achievement = re.sub(r"^[\s•\-\*]+", "", line).strip()
                if achievement:
                    current_achievements.append(achievement)

        # Save last experience
        if current_exp:
            current_exp.achievements = current_achievements
            experiences.append(current_exp)

        return experiences

    def _parse_experience_header(self, line: str) -> WorkExperience:
        """Parse a work experience header line.

        Args:
            line: Header line with company/title/dates.

        Returns:
            WorkExperience object.
        """
        # Try to extract dates
        date_pattern = r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|\d{1,2}/\d{4}|\d{4})\s*[-–—]\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|\d{1,2}/\d{4}|\d{4}|Present|Current)"
        date_match = re.search(date_pattern, line, re.IGNORECASE)

        start_date = None
        end_date = None

        if date_match:
            start_date = date_match.group(1)
            end_date = date_match.group(2)
            # Remove dates from line
            line = line[: date_match.start()] + line[date_match.end() :]

        # Clean up the line (hyphen at end to avoid escape ambiguity)
        line = line.strip(" |•*-")

        # Try to split by common separators
        if " at " in line.lower():
            # Format: "Job Title at Company Name"
            parts = re.split(r"\s+at\s+", line, flags=re.IGNORECASE)
            title = parts[0].strip() if len(parts) > 0 else "Unknown"
            company = parts[1].strip() if len(parts) > 1 else "Unknown"
        elif "|" in line:
            # Format: "Company | Title" or "Title | Company"
            parts = [p.strip() for p in line.split("|")]
            # Heuristic: company names are often shorter or have Inc/LLC
            if len(parts) >= 2:
                if any(
                    word in parts[0].lower()
                    for word in ["inc", "llc", "corp", "ltd", "technologies"]
                ):
                    company = parts[0]
                    title = parts[1]
                else:
                    title = parts[0]
                    company = parts[1]
            else:
                title = parts[0]
                company = "Unknown"
        elif "," in line:
            # Format: "Job Title, Company Name"
            parts = [p.strip() for p in line.split(",", 1)]
            title = parts[0] if len(parts) > 0 else "Unknown"
            company = parts[1] if len(parts) > 1 else "Unknown"
        else:
            # Single line - assume it's a title
            title = line
            company = "Unknown"

        return WorkExperience(
            company=company,
            title=title,
            start_date=start_date,
            end_date=end_date,
        )

    def _extract_education(self, text: str) -> list[Education]:
        """Extract education entries.

        Args:
            text: Education section text.

        Returns:
            List of Education objects.
        """
        if not text:
            return []

        education_list = []
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        current_edu = None
        current_honors = []

        for line in lines:
            # Check if it's an institution line (usually starts with capital, has date)
            date_pattern = r"\d{4}"
            has_date = re.search(date_pattern, line)

            # Common degree patterns
            degree_pattern = r"\b(BS|BA|MS|MA|MBA|PhD|Ph\.D\.|Bachelor|Master|Doctor)\b"
            has_degree = re.search(degree_pattern, line, re.IGNORECASE)

            if (
                has_date or has_degree or re.match(r"^[A-Z]", line)
            ) and len(line) < 150:
                # Save previous education
                if current_edu:
                    current_edu.honors = current_honors
                    education_list.append(current_edu)

                # Parse new education entry
                current_edu = self._parse_education_line(line)
                current_honors = []

            elif current_edu and line:
                # This is additional info (honors, GPA, etc.)
                if "gpa" in line.lower() and not current_edu.gpa:
                    gpa_match = re.search(r"(\d\.\d+)", line)
                    if gpa_match:
                        current_edu.gpa = gpa_match.group(1)
                else:
                    current_honors.append(line)

        # Save last education
        if current_edu:
            current_edu.honors = current_honors
            education_list.append(current_edu)

        return education_list

    def _parse_education_line(self, line: str) -> Education:
        """Parse an education entry line.

        Args:
            line: Education line.

        Returns:
            Education object.
        """
        # Extract graduation date
        date_pattern = r"\b(19|20)\d{2}\b"
        date_match = re.search(date_pattern, line)
        graduation_date = date_match.group(0) if date_match else None

        # Extract degree
        degree_pattern = r"\b(BS|BA|MS|MA|MBA|PhD|Ph\.D\.|Bachelor(?:'s)?|Master(?:'s)?|Doctor(?:ate)?)\b"
        degree_match = re.search(degree_pattern, line, re.IGNORECASE)
        degree = degree_match.group(0) if degree_match else None

        # Extract field (usually "in Computer Science" or similar)
        field = None
        field_pattern = r"\bin\s+([A-Z][a-zA-Z\s]+?)(?:\s*[,|]|$)"
        field_match = re.search(field_pattern, line)
        if field_match:
            field = field_match.group(1).strip()

        # Institution is usually at the start or before the degree
        institution = line.split(",")[0].strip()

        # Remove degree and date from institution name if present
        if degree_match:
            institution = line[: degree_match.start()].strip(" ,")
        if not institution or len(institution) < 3:
            institution = "Unknown"

        return Education(
            institution=institution,
            degree=degree,
            field=field,
            graduation_date=graduation_date,
        )

    def _extract_certifications(self, text: str) -> list[str]:
        """Extract certifications.

        Args:
            text: Certifications section text.

        Returns:
            List of certifications.
        """
        if not text:
            return []

        certifications = []
        lines = text.split("\n")

        for line in lines:
            # Remove bullet points and trim
            cert = re.sub(r"^[\s•\-\*]+", "", line).strip()
            if cert and len(cert) > 2:
                certifications.append(cert)

        return certifications
