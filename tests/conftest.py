"""
Pytest configuration and fixtures for browser tests.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_page():
    """Create a mock Playwright page."""
    page = MagicMock()
    page.url = "https://www.linkedin.com/feed/"
    page.goto = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.query_selector = AsyncMock(return_value=None)
    page.query_selector_all = AsyncMock(return_value=[])
    page.keyboard = MagicMock()
    page.keyboard.press = AsyncMock()
    page.mouse = MagicMock()
    page.mouse.move = AsyncMock()
    page.mouse.click = AsyncMock()
    page.mouse.wheel = AsyncMock()
    page.screenshot = AsyncMock()
    page.close = AsyncMock()
    page.add_init_script = AsyncMock()
    return page


@pytest.fixture
def mock_browser():
    """Create a mock LinkedInBrowser."""
    browser = MagicMock()
    browser.random_delay = AsyncMock()
    browser.goto = AsyncMock()
    browser.human_type = AsyncMock()
    browser.human_click = AsyncMock()
    browser.scroll_page = AsyncMock()
    browser.scroll_to_element = AsyncMock()
    browser.wait_for_element = AsyncMock(return_value=True)
    browser.element_exists = AsyncMock(return_value=False)
    browser.get_text = AsyncMock(return_value="")
    browser.get_attribute = AsyncMock(return_value="")
    browser.take_screenshot = AsyncMock()
    browser.new_page = AsyncMock()
    browser.save_cookies = AsyncMock()
    browser.load_cookies = AsyncMock(return_value=True)
    browser.start = AsyncMock()
    browser.close = AsyncMock()
    return browser


@pytest.fixture
def temp_session_dir(tmp_path):
    """Create a temporary session directory."""
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    return session_dir


@pytest.fixture
def sample_job_listing():
    """Create a sample job listing for testing."""
    from job_hunter.agent.job_searcher import JobListing

    return JobListing(
        job_id="3789456123",
        title="Chief of Staff",
        company="Acme Startup Inc",
        location="New York, NY",
        url="https://www.linkedin.com/jobs/view/3789456123",
        easy_apply=True,
        posted_date="2 days ago",
        company_size="11-50 employees",
        description="We're looking for a Chief of Staff to join our team...",
        experience_level="Mid-Senior level",
        job_type="Full-time",
    )


# Pytest hooks for integration tests
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require browser)"
    )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless --run-integration is passed."""
    if not config.getoption("--run-integration", default=False):
        skip_integration = pytest.mark.skip(reason="need --run-integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run integration tests",
    )
