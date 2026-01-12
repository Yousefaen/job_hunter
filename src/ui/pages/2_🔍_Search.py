"""Search Criteria Configuration Page."""

import streamlit as st
from pathlib import Path
import sys
import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.models.search_criteria import SearchCriteria

st.set_page_config(page_title="Search - Job Hunter", page_icon="🔍", layout="wide")

st.title("🔍 Search Configuration")
st.markdown("Configure your job search criteria.")

# Initialize search criteria if not exists
if "search_criteria" not in st.session_state:
    st.session_state.search_criteria = SearchCriteria()

criteria = st.session_state.search_criteria

# Main configuration
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Job Titles")
    st.caption("Enter job titles to search for (one per line)")

    titles_text = st.text_area(
        "Job Titles",
        value="\n".join(criteria.titles),
        height=150,
        label_visibility="collapsed",
        help="Enter each job title on a new line"
    )

    st.markdown("### Locations")
    st.caption("Enter locations to search in (one per line)")

    locations_text = st.text_area(
        "Locations",
        value="\n".join(criteria.locations),
        height=120,
        label_visibility="collapsed",
        help="Enter city, state or 'Remote'"
    )

with col2:
    st.markdown("### Experience Level")
    experience_options = [
        "Entry level",
        "Associate",
        "Mid-Senior level",
        "Senior level",
        "Director",
        "Executive"
    ]
    selected_experience = st.multiselect(
        "Experience Level",
        options=experience_options,
        default=[e for e in criteria.experience_levels if e in experience_options],
        label_visibility="collapsed"
    )

    st.markdown("### Company Size")
    st.caption("Filter by company size (proxy for startup stage)")
    size_options = [
        "1-10 employees",
        "11-50 employees",
        "51-200 employees",
        "201-500 employees",
        "501-1000 employees",
        "1001-5000 employees",
        "5001-10000 employees",
        "10001+ employees"
    ]
    selected_sizes = st.multiselect(
        "Company Size",
        options=size_options,
        default=[s for s in criteria.company_sizes if s in size_options],
        label_visibility="collapsed"
    )

    st.markdown("### Date Posted")
    date_options = ["Past 24 hours", "Past week", "Past month", "Any time"]
    selected_date = st.selectbox(
        "Date Posted",
        options=date_options,
        index=date_options.index(criteria.date_posted) if criteria.date_posted in date_options else 1,
        label_visibility="collapsed"
    )

st.markdown("---")

# Additional filters
st.markdown("### Additional Filters")

filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    job_type = st.selectbox(
        "Job Type",
        options=["Full-time", "Part-time", "Contract", "Temporary", "Internship"],
        index=0
    )

with filter_col2:
    easy_apply_only = st.checkbox(
        "Easy Apply Only",
        value=criteria.easy_apply_only,
        help="Only show jobs with LinkedIn Easy Apply"
    )

with filter_col3:
    min_score = st.slider(
        "Minimum Match Score",
        min_value=0,
        max_value=100,
        value=criteria.min_match_score,
        step=5,
        help="Only show jobs with match score above this threshold"
    )

st.markdown("---")

# Exclusions
st.markdown("### Exclusions")

excl_col1, excl_col2, excl_col3 = st.columns(3)

with excl_col1:
    st.caption("Excluded Locations")
    excluded_locations_text = st.text_area(
        "Excluded Locations",
        value="\n".join(criteria.excluded_locations),
        height=100,
        label_visibility="collapsed",
        help="Jobs in these locations will be filtered out"
    )

with excl_col2:
    st.caption("Excluded Companies")
    excluded_companies_text = st.text_area(
        "Excluded Companies",
        value="\n".join(criteria.excluded_companies),
        height=100,
        label_visibility="collapsed",
        help="Jobs from these companies will be filtered out"
    )

with excl_col3:
    st.caption("Excluded Keywords")
    excluded_keywords_text = st.text_area(
        "Excluded Keywords",
        value="\n".join(criteria.excluded_keywords),
        height=100,
        label_visibility="collapsed",
        help="Jobs containing these keywords will be filtered out"
    )

st.markdown("---")

# Save button
save_col1, save_col2, save_col3 = st.columns([1, 1, 1])

with save_col1:
    if st.button("💾 Save Configuration", use_container_width=True, type="primary"):
        # Parse text inputs
        new_titles = [t.strip() for t in titles_text.split("\n") if t.strip()]
        new_locations = [l.strip() for l in locations_text.split("\n") if l.strip()]
        new_excluded_locations = [l.strip() for l in excluded_locations_text.split("\n") if l.strip()]
        new_excluded_companies = [c.strip() for c in excluded_companies_text.split("\n") if c.strip()]
        new_excluded_keywords = [k.strip() for k in excluded_keywords_text.split("\n") if k.strip()]

        # Update criteria
        st.session_state.search_criteria = SearchCriteria(
            titles=new_titles if new_titles else ["Chief of Staff"],
            locations=new_locations if new_locations else ["Remote"],
            experience_levels=selected_experience,
            company_sizes=selected_sizes,
            date_posted=selected_date,
            job_type=job_type,
            easy_apply_only=easy_apply_only,
            min_match_score=min_score,
            excluded_locations=new_excluded_locations,
            excluded_companies=new_excluded_companies,
            excluded_keywords=new_excluded_keywords
        )
        st.success("✅ Configuration saved!")

with save_col2:
    if st.button("🔄 Reset to Defaults", use_container_width=True):
        st.session_state.search_criteria = SearchCriteria()
        st.rerun()

with save_col3:
    # Export as YAML
    yaml_content = yaml.dump(criteria.model_dump(), default_flow_style=False)
    st.download_button(
        "📥 Export YAML",
        yaml_content,
        "search_criteria.yaml",
        "text/yaml",
        use_container_width=True
    )

# Preview
st.markdown("---")
st.markdown("### Configuration Preview")

preview_col1, preview_col2 = st.columns(2)

with preview_col1:
    with st.expander("🔍 Search Parameters", expanded=True):
        st.markdown(f"**Titles:** {len(criteria.titles)}")
        for t in criteria.titles[:5]:
            st.markdown(f"  • {t}")
        if len(criteria.titles) > 5:
            st.caption(f"  ... and {len(criteria.titles) - 5} more")

        st.markdown(f"**Locations:** {len(criteria.locations)}")
        for l in criteria.locations[:5]:
            st.markdown(f"  • {l}")

        st.markdown(f"**Experience:** {', '.join(selected_experience) if selected_experience else 'Any'}")
        st.markdown(f"**Company Size:** {len(selected_sizes)} selected")
        st.markdown(f"**Date Posted:** {selected_date}")
        st.markdown(f"**Easy Apply Only:** {'Yes' if easy_apply_only else 'No'}")

with preview_col2:
    with st.expander("🚫 Exclusions", expanded=True):
        excl_locs = [l.strip() for l in excluded_locations_text.split("\n") if l.strip()]
        excl_comps = [c.strip() for c in excluded_companies_text.split("\n") if c.strip()]
        excl_kws = [k.strip() for k in excluded_keywords_text.split("\n") if k.strip()]

        st.markdown(f"**Excluded Locations:** {len(excl_locs)}")
        for l in excl_locs[:3]:
            st.markdown(f"  • {l}")

        st.markdown(f"**Excluded Companies:** {len(excl_comps)}")
        for c in excl_comps[:3]:
            st.markdown(f"  • {c}")

        st.markdown(f"**Excluded Keywords:** {len(excl_kws)}")
        st.markdown(f"**Min Match Score:** {min_score}%")

# Search button (placeholder for future functionality)
st.markdown("---")
st.markdown("### Ready to Search?")

if not st.session_state.get("profile"):
    st.warning("⚠️ Please upload a resume first before searching for jobs.")
    st.page_link("pages/1_📄_Resume.py", label="Go to Resume Page")
else:
    st.info(
        "🔍 **Coming Soon**: Live job search integration with LinkedIn. "
        "For now, you can add sample jobs in the Results page to test the matching flow."
    )
    st.page_link("pages/3_📊_Results.py", label="Go to Results Page")
