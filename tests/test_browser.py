"""
Tests for browser automation module.

These tests cover:
- Selectors structure and URL generation
- JobSearcher URL building and job ID extraction
- JobListing model conversion and updates
- LinkedInBrowser utility methods
- LinkedInAuth session management and login flow

Note: Full integration tests require a browser and LinkedIn credentials.
Run integration tests with: pytest tests/ -m integration
"""

import json
import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from job_hunter.browser.selectors import (
    Selectors,
    LoginSelectors,
    JobSearchSelectors,
    JobDetailSelectors,
    EasyApplySelectors,
    FilterSelectors,
)
from job_hunter.agent.job_searcher import (
    JobSearcher,
    JobListing,
    JobSearchError,
    NoResultsError,
)


class TestSelectors:
    """Tests for selector definitions."""

    def test_selectors_initialization(self):
        """Test that Selectors class initializes correctly."""
        selectors = Selectors()

        assert isinstance(selectors.login, LoginSelectors)
        assert isinstance(selectors.job_search, JobSearchSelectors)
        assert isinstance(selectors.job_detail, JobDetailSelectors)
        assert isinstance(selectors.easy_apply, EasyApplySelectors)
        assert isinstance(selectors.filters, FilterSelectors)

    def test_login_selectors_defined(self):
        """Test that login selectors are properly defined."""
        login = LoginSelectors()

        assert login.EMAIL_INPUT
        assert login.PASSWORD_INPUT
        assert login.SUBMIT_BUTTON

    def test_job_search_selectors_defined(self):
        """Test that job search selectors are properly defined."""
        search = JobSearchSelectors()

        assert search.JOB_CARD
        assert search.JOB_CARD_TITLE
        assert search.JOB_CARD_COMPANY

    def test_urls_defined(self):
        """Test that URLs are properly defined."""
        assert Selectors.LOGIN_URL == "https://www.linkedin.com/login"
        assert Selectors.JOBS_URL == "https://www.linkedin.com/jobs"
        assert Selectors.JOBS_SEARCH_URL == "https://www.linkedin.com/jobs/search/"

    def test_get_job_url(self):
        """Test job URL generation."""
        url = Selectors.get_job_url("12345678")
        assert url == "https://www.linkedin.com/jobs/view/12345678"

    def test_get_company_url(self):
        """Test company URL generation."""
        url = Selectors.get_company_url("acme-corp")
        assert url == "https://www.linkedin.com/company/acme-corp"


class TestJobListing:
    """Tests for JobListing dataclass."""

    def test_job_listing_creation(self):
        """Test creating a JobListing."""
        job = JobListing(
            job_id="12345",
            title="Chief of Staff",
            company="Acme Inc",
            location="New York, NY",
            url="https://www.linkedin.com/jobs/view/12345",
            easy_apply=True,
        )

        assert job.job_id == "12345"
        assert job.title == "Chief of Staff"
        assert job.company == "Acme Inc"
        assert job.location == "New York, NY"
        assert job.easy_apply is True
        assert job.description is None

    def test_job_listing_defaults(self):
        """Test JobListing default values."""
        job = JobListing(
            job_id="12345",
            title="Test Job",
            company="Test Co",
            location="Remote",
            url="https://example.com",
        )

        assert job.easy_apply is False
        assert job.posted_date is None
        assert job.company_size is None
        assert job.description is None

    def test_with_details_immutable(self):
        """Test that with_details returns a new instance (immutable)."""
        original = JobListing(
            job_id="12345",
            title="Test Job",
            company="Test Co",
            location="Remote",
            url="https://example.com",
        )

        updated = original.with_details(
            description="New description",
            company_size="11-50 employees",
        )

        # Original should be unchanged
        assert original.description is None
        assert original.company_size is None

        # Updated should have new values
        assert updated.description == "New description"
        assert updated.company_size == "11-50 employees"

        # Other fields should be preserved
        assert updated.job_id == original.job_id
        assert updated.title == original.title

    def test_with_details_partial_update(self):
        """Test with_details with only some fields."""
        job = JobListing(
            job_id="12345",
            title="Test Job",
            company="Test Co",
            location="Remote",
            url="https://example.com",
            easy_apply=False,
        )

        updated = job.with_details(easy_apply=True)

        assert updated.easy_apply is True
        assert updated.description is None  # Unchanged

    def test_to_job_conversion(self):
        """Test converting JobListing to Job model."""
        job_listing = JobListing(
            job_id="12345",
            title="Chief of Staff",
            company="Acme Inc",
            location="New York, NY",
            url="https://www.linkedin.com/jobs/view/12345",
            easy_apply=True,
            description="Test description",
            company_size="11-50 employees",
            experience_level="Mid-Senior level",
            job_type="Full-time",
        )

        # This test requires the core models to be available
        try:
            job = job_listing.to_job()

            assert job.job_id == "12345"
            assert job.title == "Chief of Staff"
            assert job.company == "Acme Inc"
            assert job.location == "New York, NY"
            assert job.easy_apply is True
            assert job.description == "Test description"
            assert job.company_size == "11-50 employees"
        except ImportError:
            pytest.skip("Core models not available")

    def test_to_job_with_empty_description(self):
        """Test to_job conversion handles None description."""
        job_listing = JobListing(
            job_id="12345",
            title="Test Job",
            company="Test Co",
            location="Remote",
            url="https://example.com",
            description=None,
        )

        try:
            job = job_listing.to_job()
            assert job.description == ""  # Should default to empty string
        except ImportError:
            pytest.skip("Core models not available")


class TestJobSearcher:
    """Tests for JobSearcher class."""

    @pytest.fixture
    def mock_browser(self):
        """Create a mock browser instance."""
        browser = MagicMock()
        browser.random_delay = AsyncMock()
        browser.goto = AsyncMock()
        browser.wait_for_element = AsyncMock(return_value=True)
        browser.element_exists = AsyncMock(return_value=False)
        return browser

    @pytest.fixture
    def searcher(self, mock_browser):
        """Create a JobSearcher with mock browser."""
        return JobSearcher(mock_browser)

    def test_build_search_url_basic(self, searcher):
        """Test basic search URL generation."""
        url = searcher.build_search_url(
            keywords="Chief of Staff",
            location="New York",
        )

        assert "keywords=Chief+of+Staff" in url or "keywords=Chief%20of%20Staff" in url
        assert "location=New+York" in url or "location=New%20York" in url
        assert "f_AL=true" in url  # Easy Apply default

    def test_build_search_url_with_date_filter(self, searcher):
        """Test search URL with date filter."""
        url = searcher.build_search_url(
            keywords="Developer",
            location="Remote",
            date_posted="Past week",
        )

        assert "f_TPR=r604800" in url

    def test_build_search_url_with_experience_filter(self, searcher):
        """Test search URL with experience level filter."""
        url = searcher.build_search_url(
            keywords="Manager",
            location="NYC",
            experience_levels=["Mid-Senior level", "Director"],
        )

        assert "f_E=4%2C5" in url or "f_E=4,5" in url

    def test_build_search_url_with_job_type(self, searcher):
        """Test search URL with job type filter."""
        url = searcher.build_search_url(
            keywords="Engineer",
            location="SF",
            job_types=["Full-time", "Contract"],
        )

        assert "f_JT=F%2CC" in url or "f_JT=F,C" in url

    def test_build_search_url_pagination(self, searcher):
        """Test search URL with pagination."""
        url = searcher.build_search_url(
            keywords="Analyst",
            location="Boston",
            start=25,
        )

        assert "start=25" in url

    def test_build_search_url_easy_apply_disabled(self, searcher):
        """Test search URL without Easy Apply filter."""
        url = searcher.build_search_url(
            keywords="Designer",
            location="LA",
            easy_apply_only=False,
        )

        assert "f_AL" not in url

    def test_extract_job_id_from_view_url(self, searcher):
        """Test job ID extraction from view URL."""
        url = "https://www.linkedin.com/jobs/view/3789456123"
        job_id = searcher._extract_job_id(url)
        assert job_id == "3789456123"

    def test_extract_job_id_from_query_param(self, searcher):
        """Test job ID extraction from query parameter."""
        url = "https://www.linkedin.com/jobs/search/?currentJobId=3789456123"
        job_id = searcher._extract_job_id(url)
        assert job_id == "3789456123"

    def test_extract_job_id_invalid_url(self, searcher):
        """Test job ID extraction from invalid URL."""
        url = "https://www.linkedin.com/in/profile"
        job_id = searcher._extract_job_id(url)
        assert job_id is None

    def test_date_posted_filter_mapping(self, searcher):
        """Test date posted filter value mapping."""
        assert searcher.DATE_POSTED_FILTERS["Past 24 hours"] == "r86400"
        assert searcher.DATE_POSTED_FILTERS["Past week"] == "r604800"
        assert searcher.DATE_POSTED_FILTERS["Past month"] == "r2592000"

    def test_experience_level_filter_mapping(self, searcher):
        """Test experience level filter value mapping."""
        assert searcher.EXPERIENCE_LEVEL_FILTERS["Entry level"] == "2"
        assert searcher.EXPERIENCE_LEVEL_FILTERS["Mid-Senior level"] == "4"
        assert searcher.EXPERIENCE_LEVEL_FILTERS["Executive"] == "6"

    def test_job_type_filter_mapping(self, searcher):
        """Test job type filter value mapping."""
        assert searcher.JOB_TYPE_FILTERS["Full-time"] == "F"
        assert searcher.JOB_TYPE_FILTERS["Part-time"] == "P"
        assert searcher.JOB_TYPE_FILTERS["Contract"] == "C"

    def test_senior_level_filter_exists(self, searcher):
        """Test that Senior level is mapped correctly."""
        assert "Senior level" in searcher.EXPERIENCE_LEVEL_FILTERS
        assert searcher.EXPERIENCE_LEVEL_FILTERS["Senior level"] == "4"

    @pytest.mark.asyncio
    async def test_wait_for_listings_success(self, mock_browser):
        """Test _wait_for_listings returns True when container found."""
        mock_browser.wait_for_element = AsyncMock(return_value=True)
        mock_browser.element_exists = AsyncMock(return_value=False)

        mock_page = MagicMock()
        searcher = JobSearcher(mock_browser)

        result = await searcher._wait_for_listings(mock_page)

        assert result is True

    @pytest.mark.asyncio
    async def test_wait_for_listings_no_results(self, mock_browser):
        """Test _wait_for_listings returns False when no results banner found."""
        # Simulate "no results" banner being present
        mock_browser.element_exists = AsyncMock(return_value=True)

        mock_page = MagicMock()
        searcher = JobSearcher(mock_browser)

        result = await searcher._wait_for_listings(mock_page)

        assert result is False

    @pytest.mark.asyncio
    async def test_wait_for_listings_timeout(self, mock_browser):
        """Test _wait_for_listings returns False on timeout."""
        mock_browser.element_exists = AsyncMock(return_value=False)
        mock_browser.wait_for_element = AsyncMock(return_value=False)

        mock_page = MagicMock()
        searcher = JobSearcher(mock_browser)

        result = await searcher._wait_for_listings(mock_page)

        assert result is False


class TestNoResultsError:
    """Tests for NoResultsError exception."""

    def test_no_results_error_inheritance(self):
        """Test NoResultsError inherits from JobSearchError."""
        assert issubclass(NoResultsError, JobSearchError)

    def test_no_results_error_message(self):
        """Test NoResultsError can be raised with message."""
        with pytest.raises(NoResultsError, match="No jobs found"):
            raise NoResultsError("No jobs found for query")


class TestLinkedInBrowser:
    """Tests for LinkedInBrowser class."""

    def test_user_agents_defined(self):
        """Test that user agents are defined."""
        from job_hunter.browser.linkedin_browser import LinkedInBrowser

        assert len(LinkedInBrowser.USER_AGENTS) > 0
        assert all("Mozilla" in ua for ua in LinkedInBrowser.USER_AGENTS)

    def test_viewport_sizes_defined(self):
        """Test that viewport sizes are defined."""
        from job_hunter.browser.linkedin_browser import LinkedInBrowser

        assert len(LinkedInBrowser.VIEWPORT_SIZES) > 0
        for size in LinkedInBrowser.VIEWPORT_SIZES:
            assert "width" in size
            assert "height" in size
            assert size["width"] > 0
            assert size["height"] > 0

    def test_browser_initialization(self):
        """Test browser initialization with default values."""
        from job_hunter.browser.linkedin_browser import LinkedInBrowser

        browser = LinkedInBrowser()

        assert browser.headless is False
        assert browser.min_delay == 30.0
        assert browser.max_delay == 90.0
        assert browser.slow_mo == 50

    def test_browser_initialization_custom_values(self):
        """Test browser initialization with custom values."""
        from job_hunter.browser.linkedin_browser import LinkedInBrowser

        browser = LinkedInBrowser(
            headless=True,
            min_delay=10.0,
            max_delay=30.0,
            slow_mo=100,
        )

        assert browser.headless is True
        assert browser.min_delay == 10.0
        assert browser.max_delay == 30.0
        assert browser.slow_mo == 100


class TestLinkedInAuth:
    """Tests for LinkedInAuth class."""

    @pytest.fixture
    def mock_browser(self):
        """Create a mock browser for auth tests."""
        browser = MagicMock()
        browser.random_delay = AsyncMock()
        browser.goto = AsyncMock()
        browser.human_type = AsyncMock()
        browser.human_click = AsyncMock()
        browser.element_exists = AsyncMock(return_value=False)
        browser.new_page = AsyncMock()
        browser.take_screenshot = AsyncMock()
        browser.load_cookies = AsyncMock(return_value=True)
        browser.save_cookies = AsyncMock()
        browser.wait_for_element = AsyncMock(return_value=True)
        browser.get_text = AsyncMock(return_value="")
        return browser

    @pytest.fixture
    def mock_page(self):
        """Create a mock page for auth tests."""
        page = MagicMock()
        page.url = "https://www.linkedin.com/feed/"
        page.close = AsyncMock()
        return page

    def test_auth_initialization(self, mock_browser):
        """Test auth initialization."""
        from job_hunter.browser.login import LinkedInAuth

        auth = LinkedInAuth(mock_browser)

        assert auth.browser == mock_browser
        assert auth.is_authenticated is False
        assert auth.session_dir == Path("data/sessions")

    def test_auth_custom_session_dir(self, mock_browser):
        """Test auth with custom session directory."""
        from job_hunter.browser.login import LinkedInAuth

        custom_dir = Path("/tmp/test_sessions")
        auth = LinkedInAuth(mock_browser, session_dir=custom_dir)

        assert auth.session_dir == custom_dir

    def test_cookie_path(self, mock_browser):
        """Test cookie file path generation."""
        from job_hunter.browser.login import LinkedInAuth

        auth = LinkedInAuth(mock_browser)

        assert auth.cookie_path == Path("data/sessions/linkedin_cookies.json")

    @pytest.mark.asyncio
    async def test_login_missing_credentials(self, mock_browser, mock_page):
        """Test login fails without credentials."""
        from job_hunter.browser.login import LinkedInAuth, AuthenticationError

        auth = LinkedInAuth(mock_browser)

        with pytest.raises(AuthenticationError, match="credentials not provided"):
            await auth.login(page=mock_page)

    @pytest.mark.asyncio
    async def test_login_success_redirect_to_feed(self, mock_browser, mock_page):
        """Test successful login when redirected to feed."""
        from job_hunter.browser.login import LinkedInAuth

        # Simulate redirect to feed after navigation
        mock_page.url = "https://www.linkedin.com/feed/"
        mock_browser.new_page = AsyncMock(return_value=mock_page)

        auth = LinkedInAuth(mock_browser)
        result = await auth.login(
            email="test@example.com",
            password="password123",
            page=mock_page,
        )

        assert result is True
        assert auth.is_authenticated is True

    def test_session_validity_check(self, mock_browser, tmp_path):
        """Test session validity checking with metadata."""
        from job_hunter.browser.login import LinkedInAuth

        auth = LinkedInAuth(mock_browser, session_dir=tmp_path)

        # Create valid session metadata
        meta = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "version": "1.0",
        }
        meta_path = tmp_path / "session_meta.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f)

        # Should return True for valid session
        assert auth._is_session_valid() is True

    def test_session_validity_expired(self, mock_browser, tmp_path):
        """Test expired session is detected."""
        from job_hunter.browser.login import LinkedInAuth
        from datetime import timedelta

        auth = LinkedInAuth(mock_browser, session_dir=tmp_path)

        # Create expired session metadata (8 days old)
        old_time = datetime.now(timezone.utc) - timedelta(days=8)
        meta = {
            "saved_at": old_time.isoformat(),
            "version": "1.0",
        }
        meta_path = tmp_path / "session_meta.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f)

        # Should return False for expired session
        assert auth._is_session_valid() is False

    def test_session_validity_no_file(self, mock_browser, tmp_path):
        """Test session validity when no metadata file exists."""
        from job_hunter.browser.login import LinkedInAuth

        auth = LinkedInAuth(mock_browser, session_dir=tmp_path)

        # Should return False when no metadata file exists
        assert auth._is_session_valid() is False

    @pytest.mark.asyncio
    async def test_restore_session_no_cookies(self, mock_browser, tmp_path):
        """Test session restore when no cookies exist."""
        from job_hunter.browser.login import LinkedInAuth

        auth = LinkedInAuth(mock_browser, session_dir=tmp_path)

        result = await auth.restore_session()

        assert result is False
        assert auth.is_authenticated is False


class TestIntegration:
    """Integration tests that require actual browser.

    These tests are skipped by default and can be run with:
    pytest tests/ -m integration --run-integration
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_browser_starts_and_stops(self):
        """Test that browser can start and stop cleanly."""
        from job_hunter.browser.linkedin_browser import LinkedInBrowser

        browser = LinkedInBrowser(headless=True)

        await browser.start()
        assert browser.browser is not None
        assert browser.context is not None

        await browser.close()
        assert browser.browser is None
        assert browser.context is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_page_navigation(self):
        """Test page navigation works."""
        from job_hunter.browser.linkedin_browser import LinkedInBrowser

        async with LinkedInBrowser(headless=True, min_delay=0.1, max_delay=0.2) as browser:
            page = await browser.new_page()
            await browser.goto(page, "https://www.linkedin.com")

            assert "linkedin" in page.url
            await page.close()
