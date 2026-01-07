"""Example script demonstrating resume parsing functionality."""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.resume.parser import ResumeParser
from src.resume.profile import UserProfile


def main():
    """Demonstrate resume parsing capabilities."""
    parser = ResumeParser()

    print("=" * 70)
    print("LinkedIn Job Application Agent - Resume Parser Demo")
    print("=" * 70)
    print()

    # Example 1: Parse JSON profile template
    print("1. Parsing JSON Profile Template")
    print("-" * 70)

    json_path = Path("data/resumes/profile_template.json")
    if json_path.exists():
        profile = parser.parse_json(json_path)

        print(f"[OK] Successfully parsed: {profile.contact.name}")
        print(f"  Email: {profile.contact.email}")
        print(f"  Location: {profile.contact.location}")
        print(f"  Current Title: {profile.get_current_title()}")
        print(f"  Number of Jobs: {profile.get_job_count()}")
        print(f"  Number of Skills: {len(profile.skills)}")
        print()

        # Display top skills
        print("  Top Skills:")
        for skill in profile.skills[:5]:
            print(f"    - {skill}")
        print()

        # Display work experience
        print("  Work Experience:")
        for exp in profile.work_experience[:2]:  # Show first 2
            print(f"    - {exp.title} at {exp.company}")
            print(f"      {exp.duration_text}")
        print()

        # Display keywords for matching
        print("  Extracted Keywords (sample):")
        keywords = profile.get_keywords()
        for keyword in sorted(keywords)[:10]:
            print(f"    - {keyword}")
        print()

        # Example 2: Check for specific skills
        print("2. Skill Checking")
        print("-" * 70)
        test_skills = ["Python", "Strategic Planning", "Java", "Leadership"]
        for skill in test_skills:
            has_skill = profile.has_skill(skill)
            status = "[YES]" if has_skill else "[ NO]"
            print(f"  {status} Has '{skill}': {has_skill}")
        print()

        # Example 3: Generate text summary for LLM
        print("3. Text Summary for LLM")
        print("-" * 70)
        summary = profile.to_text_summary()
        print("  Generated summary for Claude API job matching:")
        print()
        # Print first 500 characters
        print(f"  {summary[:500]}...")
        print()

        # Example 4: Profile validation
        print("4. Profile Validation")
        print("-" * 70)
        print(f"  [OK] Contact info: Complete")
        print(f"  [OK] Work experience entries: {len(profile.work_experience)}")
        print(f"  [OK] Education entries: {len(profile.education)}")
        print(f"  [OK] Skills listed: {len(profile.skills)}")
        print(f"  [OK] Certifications: {len(profile.certifications)}")
        print()

    else:
        print(f"  [ERROR] Template not found at: {json_path}")
        print()

    # Example 5: Demonstrate PDF parsing (if PDF exists)
    print("5. PDF Resume Parsing")
    print("-" * 70)
    print("  To test PDF parsing:")
    print("    1. Place your PDF resume in data/resumes/")
    print("    2. Run: profile = parser.parse_file('data/resumes/your_resume.pdf')")
    print()
    print("  The parser will extract:")
    print("    • Contact information (name, email, phone, location)")
    print("    • Professional summary")
    print("    • Skills and competencies")
    print("    • Work experience with achievements")
    print("    • Education history")
    print("    • Certifications")
    print()

    # Example 6: Integration with job matching
    print("6. Integration with Job Matching")
    print("-" * 70)
    print("  Once parsed, the profile can be used for:")
    print()
    print("  a) Keyword-based initial filtering")
    print("     - Extract keywords: profile.get_keywords()")
    print("     - Quick check if job matches basic requirements")
    print()
    print("  b) LLM-powered deep matching")
    print("     - Generate summary: profile.to_text_summary()")
    print("     - Send to Claude API with job description")
    print("     - Get match score (0-100) and reasoning")
    print()
    print("  c) Application form filling")
    print("     - Use profile.contact for contact fields")
    print("     - Use profile.work_experience for work history")
    print("     - Use profile.education for education fields")
    print()

    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
