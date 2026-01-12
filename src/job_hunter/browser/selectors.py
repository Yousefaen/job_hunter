"""
LinkedIn CSS/XPath selectors for browser automation.

Note: LinkedIn frequently updates their UI, so selectors may need periodic updates.
Selectors are organized by page/feature for easier maintenance.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LoginSelectors:
    """Selectors for LinkedIn login page."""

    # Login form
    EMAIL_INPUT: str = 'input[id="username"]'
    PASSWORD_INPUT: str = 'input[id="password"]'
    SUBMIT_BUTTON: str = 'button[type="submit"]'

    # Alternative login selectors (for different login flows)
    EMAIL_INPUT_ALT: str = 'input[name="session_key"]'
    PASSWORD_INPUT_ALT: str = 'input[name="session_password"]'

    # Post-login indicators
    FEED_CONTAINER: str = 'div[data-test-id="feed-container"]'
    NAV_PROFILE: str = 'div[data-control-name="nav.settings_signout"]'
    GLOBAL_NAV: str = 'header[id="global-nav"]'

    # Error messages
    LOGIN_ERROR: str = 'div[id="error-for-username"], div[id="error-for-password"]'
    CAPTCHA_CHALLENGE: str = 'div[id="captcha-challenge"]'

    # 2FA / Security verification
    VERIFICATION_CODE_INPUT: str = 'input[id="input__phone_verification_pin"]'
    VERIFICATION_PROMPT: str = 'h1:has-text("Let\'s do a quick security check")'


@dataclass(frozen=True)
class JobSearchSelectors:
    """Selectors for LinkedIn job search page."""

    # Search inputs (use partial match - ember suffix is dynamic)
    KEYWORD_INPUT: str = 'input[id^="jobs-search-box-keyword"]'
    LOCATION_INPUT: str = 'input[id^="jobs-search-box-location"]'
    SEARCH_BUTTON: str = 'button[data-tracking-control-name="public_jobs_jobs-search-bar_base-search-bar-search-submit"]'

    # Alternative search (logged in view)
    SEARCH_INPUT_LOGGED_IN: str = 'input.jobs-search-box__text-input'
    KEYWORD_INPUT_ALT: str = 'input[aria-label="Search by title, skill, or company"]'
    LOCATION_INPUT_ALT: str = 'input[aria-label="City, state, or zip code"]'

    # Job listings container
    JOBS_LIST_CONTAINER: str = 'ul.jobs-search__results-list'
    JOBS_LIST_CONTAINER_ALT: str = 'div.jobs-search-results-list'
    SCAFFOLD_LIST: str = 'div.scaffold-layout__list'

    # Individual job cards
    JOB_CARD: str = 'li.jobs-search-results__list-item'
    JOB_CARD_ALT: str = 'div.job-card-container'
    JOB_CARD_LINK: str = 'a.job-card-container__link'
    JOB_CARD_TITLE: str = 'a.job-card-list__title'
    JOB_CARD_TITLE_ALT: str = 'span.job-card-list__title'
    JOB_CARD_COMPANY: str = 'span.job-card-container__primary-description'
    JOB_CARD_COMPANY_ALT: str = 'a.job-card-container__company-name'
    JOB_CARD_LOCATION: str = 'li.job-card-container__metadata-item'
    JOB_CARD_METADATA: str = 'ul.job-card-container__metadata-wrapper'

    # Job card status indicators
    EASY_APPLY_BADGE: str = 'li.job-card-container__apply-method'
    EASY_APPLY_ICON: str = 'svg[data-test-icon="linkedin-bug-small"]'
    PROMOTED_BADGE: str = 'span:has-text("Promoted")'

    # Pagination
    PAGINATION_CONTAINER: str = 'div.jobs-search-results-list__pagination'
    PAGINATION_BUTTON: str = 'button[aria-label*="Page"]'
    NEXT_PAGE_BUTTON: str = 'button[aria-label="Next"]'
    PAGE_NUMBER: str = 'li[data-test-pagination-page-btn]'

    # Loading states
    LOADING_SPINNER: str = 'div.jobs-search-results-list__loader'
    SKELETON_LOADER: str = 'div.job-card-container--loading'

    # No results / empty states
    NO_RESULTS: str = 'div.jobs-search-no-results-banner'
    NO_RESULTS_ALT: str = 'h1:has-text("No matching jobs found")'
    SUGGESTED_JOBS: str = 'div.jobs-search-similar-jobs'


@dataclass(frozen=True)
class JobDetailSelectors:
    """Selectors for job detail panel/page."""

    # Job detail container
    DETAIL_CONTAINER: str = 'div.jobs-details'
    DETAIL_PANEL: str = 'div.jobs-search__job-details'

    # Job header info
    JOB_TITLE: str = 'h1.job-details-jobs-unified-top-card__job-title'
    JOB_TITLE_ALT: str = 'h2.jobs-unified-top-card__job-title'
    COMPANY_NAME: str = 'a.job-details-jobs-unified-top-card__company-name'
    COMPANY_NAME_ALT: str = 'span.job-details-jobs-unified-top-card__company-name'
    COMPANY_LINK: str = 'a[data-tracking-control-name="public_jobs_topcard-org-name"]'
    LOCATION: str = 'span.job-details-jobs-unified-top-card__bullet'
    POSTED_DATE: str = 'span.job-details-jobs-unified-top-card__posted-date'

    # Job metadata
    JOB_INSIGHTS: str = 'li.job-details-jobs-unified-top-card__job-insight'
    WORKPLACE_TYPE: str = 'span.job-details-jobs-unified-top-card__workplace-type'
    APPLICANT_COUNT: str = 'span.job-details-jobs-unified-top-card__applicant-count'

    # Job description
    DESCRIPTION_CONTAINER: str = 'div.jobs-description'
    DESCRIPTION_CONTENT: str = 'div.jobs-description-content__text'
    DESCRIPTION_TEXT: str = 'div.jobs-box__html-content'
    SHOW_MORE_BUTTON: str = 'button.jobs-description__footer-button'

    # Company info in detail
    COMPANY_SIZE: str = 'li.job-details-jobs-unified-top-card__job-insight span:has-text("employees")'
    COMPANY_INDUSTRY: str = 'li.job-details-jobs-unified-top-card__job-insight span'

    # Apply section
    APPLY_BUTTON: str = 'button.jobs-apply-button'
    EASY_APPLY_BUTTON: str = 'button.jobs-apply-button--top-card'
    EASY_APPLY_BUTTON_ALT: str = 'button:has-text("Easy Apply")'
    SAVE_BUTTON: str = 'button.jobs-save-button'

    # Job ID extraction
    JOB_ID_PATTERN: str = r'/jobs/view/(\d+)'


@dataclass(frozen=True)
class EasyApplySelectors:
    """Selectors for Easy Apply modal/form."""

    # Modal container
    MODAL_CONTAINER: str = 'div.jobs-easy-apply-modal'
    MODAL_CONTENT: str = 'div.jobs-easy-apply-content'

    # Form navigation
    NEXT_BUTTON: str = 'button[aria-label="Continue to next step"]'
    NEXT_BUTTON_ALT: str = 'button:has-text("Next")'
    REVIEW_BUTTON: str = 'button[aria-label="Review your application"]'
    REVIEW_BUTTON_ALT: str = 'button:has-text("Review")'
    SUBMIT_BUTTON: str = 'button[aria-label="Submit application"]'
    SUBMIT_BUTTON_ALT: str = 'button:has-text("Submit application")'
    CLOSE_BUTTON: str = 'button[aria-label="Dismiss"]'
    CLOSE_BUTTON_ALT: str = 'button.artdeco-modal__dismiss'

    # Form fields - Contact info
    EMAIL_INPUT: str = 'input[id*="email"]'
    PHONE_INPUT: str = 'input[id*="phone"]'
    PHONE_COUNTRY_CODE: str = 'select[id*="phoneNumber-country"]'

    # Form fields - Resume
    RESUME_UPLOAD: str = 'input[type="file"][id*="resume"]'
    RESUME_SELECT: str = 'div[data-test-single-typeahead-entity-form-component]'
    RESUME_OPTION: str = 'div[data-test-single-typeahead-entity-form-component] li'

    # Form fields - Common questions
    TEXT_INPUT: str = 'input[type="text"]'
    TEXT_AREA: str = 'textarea'
    SELECT_DROPDOWN: str = 'select'
    RADIO_BUTTON: str = 'input[type="radio"]'
    CHECKBOX: str = 'input[type="checkbox"]'

    # Form field labels
    FORM_FIELD_LABEL: str = 'label.artdeco-text-input--label'
    FORM_FIELD_LEGEND: str = 'legend.fb-form-element-label'
    REQUIRED_INDICATOR: str = 'span.fb-form-element-required'

    # Question containers
    QUESTION_CONTAINER: str = 'div.jobs-easy-apply-form-section__grouping'
    QUESTION_FIELDSET: str = 'fieldset[data-test-form-builder-radio-button-form-component]'

    # Validation and errors
    ERROR_MESSAGE: str = 'div[data-test-form-element-error-message]'
    FIELD_ERROR: str = 'span.artdeco-inline-feedback__message'

    # Progress indicator
    PROGRESS_BAR: str = 'progress.jobs-easy-apply-modal__progress-bar'
    STEP_INDICATOR: str = 'span.jobs-easy-apply-modal__step-number'

    # Success states
    SUCCESS_MESSAGE: str = 'h2:has-text("Your application was sent")'
    APPLICATION_SUBMITTED: str = 'div[data-test-post-apply-modal]'


@dataclass(frozen=True)
class FilterSelectors:
    """Selectors for job search filters."""

    # Filter buttons
    ALL_FILTERS_BUTTON: str = 'button[aria-label="Show all filters"]'
    DATE_POSTED_FILTER: str = 'button[id*="date-posted-filter"]'
    EXPERIENCE_LEVEL_FILTER: str = 'button[id*="experience-level-filter"]'
    COMPANY_SIZE_FILTER: str = 'button[id*="company-size-filter"]'
    JOB_TYPE_FILTER: str = 'button[id*="job-type-filter"]'
    EASY_APPLY_FILTER: str = 'button[id*="easy-apply-filter"]'
    LOCATION_FILTER: str = 'button[id*="location-filter"]'

    # Filter modal/dropdown
    FILTER_MODAL: str = 'div.search-reusables__filters-bar'
    FILTER_DROPDOWN: str = 'div.search-reusables__secondary-filters-values'

    # Filter options
    FILTER_CHECKBOX: str = 'input[type="checkbox"]'
    FILTER_RADIO: str = 'input[type="radio"]'
    FILTER_OPTION_LABEL: str = 'label.search-reusables__value-label'

    # Apply/Reset filters
    APPLY_FILTERS_BUTTON: str = 'button[data-control-name="filter_show_results"]'
    RESET_FILTERS_BUTTON: str = 'button:has-text("Reset")'

    # Date posted options
    DATE_PAST_24H: str = 'input[id*="timePostedRange-r86400"]'
    DATE_PAST_WEEK: str = 'input[id*="timePostedRange-r604800"]'
    DATE_PAST_MONTH: str = 'input[id*="timePostedRange-r2592000"]'

    # Experience level options
    EXP_INTERNSHIP: str = 'input[value="1"]'
    EXP_ENTRY_LEVEL: str = 'input[value="2"]'
    EXP_ASSOCIATE: str = 'input[value="3"]'
    EXP_MID_SENIOR: str = 'input[value="4"]'
    EXP_DIRECTOR: str = 'input[value="5"]'
    EXP_EXECUTIVE: str = 'input[value="6"]'


class Selectors:
    """
    Central access point for all LinkedIn selectors.

    Usage:
        selectors = Selectors()
        email_input = selectors.login.EMAIL_INPUT
        job_card = selectors.job_search.JOB_CARD
    """

    login: LoginSelectors = LoginSelectors()
    job_search: JobSearchSelectors = JobSearchSelectors()
    job_detail: JobDetailSelectors = JobDetailSelectors()
    easy_apply: EasyApplySelectors = EasyApplySelectors()
    filters: FilterSelectors = FilterSelectors()

    # Common URLs
    LOGIN_URL: str = "https://www.linkedin.com/login"
    JOBS_URL: str = "https://www.linkedin.com/jobs"
    JOBS_SEARCH_URL: str = "https://www.linkedin.com/jobs/search/"
    FEED_URL: str = "https://www.linkedin.com/feed/"

    @classmethod
    def get_job_url(cls, job_id: str) -> str:
        """Generate URL for a specific job posting."""
        return f"https://www.linkedin.com/jobs/view/{job_id}"

    @classmethod
    def get_company_url(cls, company_slug: str) -> str:
        """Generate URL for a company page."""
        return f"https://www.linkedin.com/company/{company_slug}"
