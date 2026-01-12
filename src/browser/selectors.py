"""CSS and XPath selectors for LinkedIn elements."""


class Selectors:
    """Centralized selectors for LinkedIn automation."""

    # Login page
    LOGIN_USERNAME = 'input[id="username"]'
    LOGIN_PASSWORD = 'input[id="password"]'
    LOGIN_SUBMIT = 'button[type="submit"]'
    LOGIN_REMEMBER_ME = 'input[id="rememberMeOptIn"]'

    # Navigation
    NAV_JOBS = 'a[href*="/jobs"]'
    NAV_HOME = 'a[href*="/feed"]'

    # Job search
    SEARCH_INPUT = 'input[aria-label="Search by title, skill, or company"]'
    SEARCH_LOCATION = 'input[aria-label="City, state, or zip code"]'
    SEARCH_BUTTON = 'button.jobs-search-box__submit-button'

    # Job filters
    FILTER_EASY_APPLY = 'button[aria-label="Easy Apply filter."]'
    FILTER_DATE_POSTED = 'button[aria-label="Date posted filter."]'
    FILTER_EXPERIENCE = 'button[aria-label="Experience level filter."]'
    FILTER_COMPANY_SIZE = 'button[aria-label="Company size filter."]'
    FILTER_ALL_FILTERS = 'button[aria-label="Show all filters"]'

    # Date posted options (inside filter dropdown)
    DATE_PAST_24H = 'input[id*="timePostedRange-r86400"]'
    DATE_PAST_WEEK = 'input[id*="timePostedRange-r604800"]'
    DATE_PAST_MONTH = 'input[id*="timePostedRange-r2592000"]'
    DATE_ANY_TIME = 'input[id*="timePostedRange-"]'

    # Job results
    JOB_LIST_CONTAINER = '.jobs-search-results-list'
    JOB_CARD = '.job-card-container'
    JOB_CARD_TITLE = '.job-card-list__title'
    JOB_CARD_COMPANY = '.job-card-container__company-name'
    JOB_CARD_LOCATION = '.job-card-container__metadata-item'
    JOB_CARD_EASY_APPLY = '.job-card-container__footer-item--highlighted'
    JOB_CARD_LINK = 'a.job-card-container__link'

    # Alternative selectors for job cards (LinkedIn UI variations)
    JOB_CARD_ALT = 'li.jobs-search-results__list-item'
    JOB_TITLE_ALT = '[class*="job-card-list__title"]'
    JOB_COMPANY_ALT = '[class*="artdeco-entity-lockup__subtitle"]'
    JOB_LOCATION_ALT = '[class*="artdeco-entity-lockup__caption"]'

    # Job detail panel
    JOB_DETAIL_PANEL = '.jobs-search__job-details--container'
    JOB_DETAIL_TITLE = '.job-details-jobs-unified-top-card__job-title'
    JOB_DETAIL_COMPANY = '.job-details-jobs-unified-top-card__company-name'
    JOB_DETAIL_LOCATION = '.job-details-jobs-unified-top-card__bullet'
    JOB_DETAIL_DESCRIPTION = '.jobs-description__content'
    JOB_DETAIL_EASY_APPLY = 'button.jobs-apply-button'
    JOB_DETAIL_CRITERIA = '.job-details-jobs-unified-top-card__job-insight'

    # Alternative detail selectors
    JOB_DESC_ALT = '#job-details'
    JOB_DESC_CONTENT = '.jobs-box__html-content'

    # Easy Apply modal
    EASY_APPLY_BUTTON = 'button:has-text("Easy Apply")'
    EASY_APPLY_MODAL = '.jobs-easy-apply-modal'
    EASY_APPLY_NEXT = 'button[aria-label="Continue to next step"]'
    EASY_APPLY_REVIEW = 'button[aria-label="Review your application"]'
    EASY_APPLY_SUBMIT = 'button[aria-label="Submit application"]'
    EASY_APPLY_CLOSE = 'button[aria-label="Dismiss"]'

    # Form fields
    FORM_PHONE = 'input[id*="phone"]'
    FORM_EMAIL = 'input[id*="email"]'
    FORM_RESUME_UPLOAD = 'input[type="file"]'
    FORM_TEXTAREA = 'textarea'
    FORM_SELECT = 'select'
    FORM_RADIO = 'input[type="radio"]'
    FORM_CHECKBOX = 'input[type="checkbox"]'

    # Pagination
    PAGINATION_CONTAINER = '.jobs-search-results-list__pagination'
    PAGINATION_NEXT = 'button[aria-label="Page right"]'
    PAGINATION_PAGE = 'button[aria-label*="Page"]'

    # Messages and alerts
    ALERT_ERROR = '.artdeco-inline-feedback--error'
    ALERT_SUCCESS = '.artdeco-inline-feedback--success'
    SECURITY_CHALLENGE = 'input[id="captcha"]'

    # Verification/security
    SECURITY_VERIFICATION = '#challenge'
    PIN_VERIFICATION = 'input[name="pin"]'

    @classmethod
    def get_job_card_selectors(cls) -> list[str]:
        """Get list of possible job card selectors."""
        return [cls.JOB_CARD, cls.JOB_CARD_ALT, 'div[data-job-id]']

    @classmethod
    def get_easy_apply_selectors(cls) -> list[str]:
        """Get list of possible Easy Apply button selectors."""
        return [
            cls.EASY_APPLY_BUTTON,
            'button.jobs-apply-button',
            'button[aria-label*="Easy Apply"]',
            'button:has-text("Easy Apply")',
        ]
