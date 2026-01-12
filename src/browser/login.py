"""LinkedIn authentication handling."""

import logging
import os
import time
from typing import Optional

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout

from .selectors import Selectors

logger = logging.getLogger(__name__)


class LinkedInAuth:
    """Handles LinkedIn login and session management."""

    LINKEDIN_URL = "https://www.linkedin.com"
    LOGIN_URL = "https://www.linkedin.com/login"
    FEED_URL = "https://www.linkedin.com/feed"

    def __init__(
        self,
        page: Page,
        email: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Initialize LinkedIn auth.

        Args:
            page: Playwright page object
            email: LinkedIn email (defaults to LINKEDIN_EMAIL env var)
            password: LinkedIn password (defaults to LINKEDIN_PASSWORD env var)
        """
        self.page = page
        self.email = email or os.getenv("LINKEDIN_EMAIL")
        self.password = password or os.getenv("LINKEDIN_PASSWORD")

        if not self.email or not self.password:
            logger.warning(
                "LinkedIn credentials not provided. "
                "Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables."
            )

    def is_logged_in(self) -> bool:
        """Check if already logged into LinkedIn.

        Returns:
            True if logged in
        """
        try:
            # Navigate to LinkedIn
            self.page.goto(self.LINKEDIN_URL, timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=10000)

            # Check for feed or login page
            current_url = self.page.url

            if "/feed" in current_url or "/jobs" in current_url:
                logger.info("Already logged into LinkedIn")
                return True

            # Also check for nav elements that indicate logged in state
            try:
                nav = self.page.wait_for_selector(
                    'nav[aria-label="Primary"]',
                    timeout=3000
                )
                if nav:
                    logger.info("Detected logged-in navigation")
                    return True
            except PlaywrightTimeout:
                pass

            return False

        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return False

    def login(self) -> bool:
        """Log into LinkedIn.

        Returns:
            True if login successful

        Raises:
            ValueError: If credentials not provided
        """
        if not self.email or not self.password:
            raise ValueError(
                "LinkedIn credentials required. "
                "Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables."
            )

        logger.info("Attempting LinkedIn login...")

        try:
            # Navigate to login page
            self.page.goto(self.LOGIN_URL, timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=10000)

            # Check if already logged in (redirected to feed)
            if "/feed" in self.page.url:
                logger.info("Already logged in (redirected to feed)")
                return True

            # Wait for login form
            self.page.wait_for_selector(Selectors.LOGIN_USERNAME, timeout=10000)

            # Enter email
            logger.debug("Entering email...")
            email_field = self.page.locator(Selectors.LOGIN_USERNAME)
            email_field.clear()
            email_field.type(self.email, delay=100)

            time.sleep(0.5)

            # Enter password
            logger.debug("Entering password...")
            password_field = self.page.locator(Selectors.LOGIN_PASSWORD)
            password_field.clear()
            password_field.type(self.password, delay=100)

            time.sleep(0.5)

            # Click sign in
            logger.debug("Clicking sign in...")
            self.page.click(Selectors.LOGIN_SUBMIT)

            # Wait for navigation
            time.sleep(3)

            # Check for security verification
            if self._check_security_challenge():
                logger.warning("Security challenge detected - manual intervention required")
                return self._wait_for_manual_verification()

            # Check login success
            try:
                self.page.wait_for_url("**/feed**", timeout=15000)
                logger.info("Login successful!")
                return True
            except PlaywrightTimeout:
                pass

            # Check for error messages
            error = self.page.query_selector(Selectors.ALERT_ERROR)
            if error:
                error_text = error.inner_text()
                logger.error(f"Login failed: {error_text}")
                return False

            # Check current URL
            if "/feed" in self.page.url or "/jobs" in self.page.url:
                logger.info("Login successful (verified by URL)")
                return True

            logger.warning("Login status uncertain")
            return False

        except PlaywrightTimeout as e:
            logger.error(f"Timeout during login: {e}")
            return False
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    def _check_security_challenge(self) -> bool:
        """Check if LinkedIn is showing a security challenge.

        Returns:
            True if security challenge detected
        """
        security_indicators = [
            Selectors.SECURITY_VERIFICATION,
            Selectors.SECURITY_CHALLENGE,
            Selectors.PIN_VERIFICATION,
            'text="verification"',
            'text="verify"',
            'text="security"',
        ]

        for indicator in security_indicators:
            try:
                element = self.page.query_selector(indicator)
                if element and element.is_visible():
                    return True
            except Exception:
                continue

        return False

    def _wait_for_manual_verification(self, timeout: int = 120) -> bool:
        """Wait for user to complete manual verification.

        Args:
            timeout: Maximum seconds to wait

        Returns:
            True if verification completed
        """
        logger.info(
            f"Please complete the security verification in the browser. "
            f"Waiting up to {timeout} seconds..."
        )

        start_time = time.time()

        while time.time() - start_time < timeout:
            # Check if we're now on the feed
            if "/feed" in self.page.url or "/jobs" in self.page.url:
                logger.info("Verification completed!")
                return True

            time.sleep(2)

        logger.error("Verification timeout")
        return False

    def logout(self) -> bool:
        """Log out of LinkedIn.

        Returns:
            True if logout successful
        """
        try:
            # Navigate to logout
            self.page.goto("https://www.linkedin.com/m/logout/", timeout=30000)
            time.sleep(2)

            logger.info("Logged out of LinkedIn")
            return True

        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return False

    def ensure_logged_in(self) -> bool:
        """Ensure we're logged in, logging in if necessary.

        Returns:
            True if logged in (either already or after login)
        """
        if self.is_logged_in():
            return True

        return self.login()
