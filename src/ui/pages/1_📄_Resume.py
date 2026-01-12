"""Resume Upload and Preview Page."""

import streamlit as st
from pathlib import Path
import sys
import json
import tempfile

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.resume.parser import ResumeParser
from src.resume.profile import UserProfile, ContactInfo, WorkExperience, Education

st.set_page_config(page_title="Resume - Job Hunter", page_icon="📄", layout="wide")

# Initialize session state
if "profile" not in st.session_state:
    st.session_state.profile = None

st.title("📄 Resume Management")
st.markdown("Upload your resume or create a profile manually.")

# Tabs for different input methods
tab1, tab2, tab3 = st.tabs(["📤 Upload Resume", "✏️ Manual Entry", "👁️ Preview"])

with tab1:
    st.markdown("### Upload Your Resume")
    st.markdown("Supported formats: **PDF** or **JSON**")

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["pdf", "json"],
        help="Upload your resume in PDF or JSON format"
    )

    if uploaded_file is not None:
        with st.spinner("Parsing resume..."):
            try:
                parser = ResumeParser()

                # Save to temp file for parsing
                suffix = Path(uploaded_file.name).suffix
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name

                profile = parser.parse_file(tmp_path)
                st.session_state.profile = profile

                st.success(f"✅ Successfully parsed resume for **{profile.contact.name}**")

                # Show summary
                col1, col2, col3 = st.columns(3)
                col1.metric("Skills", len(profile.skills))
                col2.metric("Experience", len(profile.work_experience))
                col3.metric("Education", len(profile.education))

            except Exception as e:
                st.error(f"❌ Error parsing resume: {str(e)}")
                st.info("💡 Try using the Manual Entry tab or ensure your PDF has extractable text.")

    # Sample JSON template
    with st.expander("📋 View JSON Template"):
        sample_json = {
            "contact": {
                "name": "Your Name",
                "email": "your.email@example.com",
                "phone": "(555) 123-4567",
                "location": "New York, NY",
                "linkedin_url": "https://linkedin.com/in/yourprofile"
            },
            "summary": "Experienced professional with...",
            "skills": ["Leadership", "Strategy", "Operations", "Data Analysis"],
            "work_experience": [
                {
                    "company": "Company Name",
                    "title": "Your Title",
                    "location": "City, State",
                    "start_date": "Jan 2020",
                    "end_date": "Present",
                    "description": "Role description",
                    "achievements": ["Achievement 1", "Achievement 2"]
                }
            ],
            "education": [
                {
                    "institution": "University Name",
                    "degree": "MBA",
                    "field": "Business Administration",
                    "graduation_date": "2019"
                }
            ],
            "certifications": [],
            "languages": ["English"]
        }
        st.json(sample_json)
        st.download_button(
            "Download Template",
            json.dumps(sample_json, indent=2),
            "resume_template.json",
            "application/json"
        )

with tab2:
    st.markdown("### Create Profile Manually")

    with st.form("manual_profile"):
        st.markdown("#### Contact Information")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name*", placeholder="John Doe")
            email = st.text_input("Email*", placeholder="john@example.com")
            phone = st.text_input("Phone", placeholder="(555) 123-4567")
        with col2:
            location = st.text_input("Location", placeholder="New York, NY")
            linkedin = st.text_input("LinkedIn URL", placeholder="https://linkedin.com/in/...")
            website = st.text_input("Website", placeholder="https://...")

        st.markdown("#### Professional Summary")
        summary = st.text_area(
            "Summary",
            placeholder="Experienced operations leader with 5+ years...",
            height=100
        )

        st.markdown("#### Skills")
        skills_input = st.text_area(
            "Skills (one per line or comma-separated)",
            placeholder="Strategic Planning\nOperations Management\nData Analysis",
            height=100
        )

        st.markdown("#### Work Experience")
        st.caption("Add your most recent position. You can add more after saving.")

        exp_col1, exp_col2 = st.columns(2)
        with exp_col1:
            exp_company = st.text_input("Company", placeholder="TechStartup Inc.")
            exp_title = st.text_input("Title", placeholder="Chief of Staff")
            exp_location = st.text_input("Job Location", placeholder="New York, NY")
        with exp_col2:
            exp_start = st.text_input("Start Date", placeholder="Jan 2020")
            exp_end = st.text_input("End Date", placeholder="Present")
            exp_desc = st.text_area("Description", placeholder="Led...", height=68)

        st.markdown("#### Education")
        edu_col1, edu_col2 = st.columns(2)
        with edu_col1:
            edu_institution = st.text_input("Institution", placeholder="Stanford University")
            edu_degree = st.text_input("Degree", placeholder="MBA")
        with edu_col2:
            edu_field = st.text_input("Field", placeholder="Business Administration")
            edu_date = st.text_input("Graduation Year", placeholder="2019")

        submitted = st.form_submit_button("💾 Save Profile", use_container_width=True)

        if submitted:
            if not name or not email:
                st.error("Name and Email are required!")
            else:
                try:
                    # Parse skills
                    if skills_input:
                        if "," in skills_input:
                            skills = [s.strip() for s in skills_input.split(",") if s.strip()]
                        else:
                            skills = [s.strip() for s in skills_input.split("\n") if s.strip()]
                    else:
                        skills = []

                    # Build profile
                    contact = ContactInfo(
                        name=name,
                        email=email,
                        phone=phone if phone else None,
                        location=location if location else None,
                        linkedin_url=linkedin if linkedin else None,
                        website=website if website else None
                    )

                    work_experience = []
                    if exp_company and exp_title:
                        work_experience.append(WorkExperience(
                            company=exp_company,
                            title=exp_title,
                            location=exp_location if exp_location else None,
                            start_date=exp_start if exp_start else None,
                            end_date=exp_end if exp_end else None,
                            description=exp_desc if exp_desc else None
                        ))

                    education = []
                    if edu_institution:
                        education.append(Education(
                            institution=edu_institution,
                            degree=edu_degree if edu_degree else None,
                            field=edu_field if edu_field else None,
                            graduation_date=edu_date if edu_date else None
                        ))

                    profile = UserProfile(
                        contact=contact,
                        summary=summary if summary else None,
                        skills=skills,
                        work_experience=work_experience,
                        education=education
                    )

                    st.session_state.profile = profile
                    st.success("✅ Profile saved successfully!")
                    st.rerun()

                except Exception as e:
                    st.error(f"Error creating profile: {str(e)}")

with tab3:
    st.markdown("### Profile Preview")

    if st.session_state.profile:
        profile = st.session_state.profile

        # Contact info card
        st.markdown("#### 👤 Contact Information")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Name:** {profile.contact.name}")
            st.markdown(f"**Email:** {profile.contact.email}")
            if profile.contact.phone:
                st.markdown(f"**Phone:** {profile.contact.phone}")
        with col2:
            if profile.contact.location:
                st.markdown(f"**Location:** {profile.contact.location}")
            if profile.contact.linkedin_url:
                st.markdown(f"**LinkedIn:** [{profile.contact.linkedin_url}]({profile.contact.linkedin_url})")

        # Summary
        if profile.summary:
            st.markdown("#### 📝 Summary")
            st.markdown(profile.summary)

        # Skills
        if profile.skills:
            st.markdown("#### 🛠️ Skills")
            # Display as tags
            skills_html = " ".join([
                f'<span style="background-color: #E1E8ED; padding: 4px 12px; border-radius: 16px; margin: 2px; display: inline-block;">{skill}</span>'
                for skill in profile.skills
            ])
            st.markdown(skills_html, unsafe_allow_html=True)

        # Work Experience
        if profile.work_experience:
            st.markdown("#### 💼 Work Experience")
            for exp in profile.work_experience:
                with st.container():
                    st.markdown(f"**{exp.title}** at **{exp.company}**")
                    meta = []
                    if exp.location:
                        meta.append(exp.location)
                    if exp.duration_text:
                        meta.append(exp.duration_text)
                    if meta:
                        st.caption(" | ".join(meta))
                    if exp.description:
                        st.markdown(exp.description)
                    if exp.achievements:
                        for ach in exp.achievements[:3]:
                            st.markdown(f"• {ach}")
                    st.markdown("---")

        # Education
        if profile.education:
            st.markdown("#### 🎓 Education")
            for edu in profile.education:
                parts = [edu.institution]
                if edu.degree:
                    parts.append(edu.degree)
                if edu.field:
                    parts.append(f"in {edu.field}")
                if edu.graduation_date:
                    parts.append(f"({edu.graduation_date})")
                st.markdown(" - ".join(parts))

        # Keywords for matching
        st.markdown("#### 🔑 Extracted Keywords (for job matching)")
        keywords = profile.get_keywords()
        if keywords:
            kw_html = " ".join([
                f'<span style="background-color: #0077B5; color: white; padding: 2px 8px; border-radius: 4px; margin: 2px; display: inline-block; font-size: 12px;">{kw}</span>'
                for kw in keywords[:20]
            ])
            st.markdown(kw_html, unsafe_allow_html=True)
            if len(keywords) > 20:
                st.caption(f"... and {len(keywords) - 20} more")

        # Export options
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 Export as JSON",
                profile.model_dump_json(indent=2),
                "my_profile.json",
                "application/json",
                use_container_width=True
            )
        with col2:
            if st.button("🗑️ Clear Profile", use_container_width=True):
                st.session_state.profile = None
                st.rerun()

    else:
        st.info("👆 Upload a resume or create a profile manually to see the preview.")
