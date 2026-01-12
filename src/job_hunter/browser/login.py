"""
LinkedIn authentication with session persistence.

Handles login, session cookies, and authentication state management.
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from playwright.async_api import Page

from job_hunter.browser.linkedin_browser import LinkedInBrowser
from job_hunter.browser.selectors import Selectors

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class TwoFactorRequired(Exception):
    """Raised when 2FA verification is needed."""
    pass


class LinkedInAuth:
    """
    Handles LinkedIn authentication and session management.

    Features:
    - Login with email/password
    - Session cookie persistence
    - Automatic session restoration
    - 2FA detection (requires manual intervention)
    - Session validity checking

    Usage:
        auth = LinkedInAuth(browser)
        if not await auth.restore_session():
            await auth.login(email, password)
    """

    DEFAULT_SESSION_DIR = Path("data/sessions")
    COOKIE_FILE = "linkedin_cookies.json"
    SESSION_METADATA_FILE = "session_meta.json"

    # Session validity duration (cookies typically last ~1 year, but we refresh more often)
    SESSION_MAX_AGE_DAYS = 7

    def __init__(
        self,
        browser: LinkedInBrowser,
        session_dir: Optional[Path] = None,
    ):
        """
        Initialize the authentication handler.

        Args:
            browser: LinkedInBrowser instance
            session_dir: Directory to store session data
        """
        self.browser = browser
        self.session_dir = session_dir or self.DEFAULT_SESSION_DIR
        self.session_dir.mkdir(parents=True, exist_ok=True)

        self._cookie_path = self.session_dir / self.COOKIE_FILE
        self._meta_path = self.session_dir / self.SESSION_METADATA_FILE
        self._is_authenticated = False

    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._is_authenticated

    @property
    def cookie_path(self) -> Path:
        """Get the cookie file path."""
        return self._cookie_path

    async def login(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        page: Optional[Page] = None,
    ) -> bool:
        """
        Login to LinkedIn with credentials.

        Args:
            email: LinkedIn email (uses LINKEDIN_EMAIL env var if not provided)
            password: LinkedIn password (uses LINKEDIN_PASSWORD env var if not provided)
            page: Existing page to use (creates new one if not provided)

        Returns:
            True if login successful

        Raises:
            AuthenticationError: If login fails
            TwoFactorRequired: If 2FA is needed
        """
        # Get credentials from environment if not provided
        email = email or os.getenv("LINKEDIN_EMAIL")
        password = password or os.getenv("LINKEDIN_PASSWORD")

        if not email or not password:
            raise AuthenticationError(
                "LinkedIn credentials not provided. Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD "
                "environment variables or pass them directly."
            )

        logger.info(f"Attempting login for {email[:3]}***@***")

        # Create page if not provided
        own_page = page is None
        if own_page:
            page = await self.browser.new_page()

        try:
            # Navigate to login page
            await self.browser.goto(page, Selectors.LOGIN_URL)
            await self.browser.random_delay(1.0, 2.0)

            # Check if already logged in (redirected to feed)
            if "feed" in page.url:
                logger.info("Already logged in (redirected to feed)")
                self._is_authenticated = True
                await self._save_session()
                return True

            # Fill in email
            await self._fill_login_field(
                page,
                Selectors.login.EMAIL_INPUT,
                Selectors.login.EMAIL_INPUT_ALT,
                email,
                "email",
            )

            # Fill in password
            await self._fill_login_field(
                page,
                Selectors.login.PASSWORD_INPUT,
                Selectors.login.PASSWORD_INPUT_ALT,
                password,
                "password",
            )

            # Click submit
            await self.browser.human_click(page, Selectors.login.SUBMIT_BUTTON)
            await self.browser.random_delay(3.0, 5.0)

            # Check for various outcomes
            await self._check_login_result(page)

            # If we get here, login was successful
            self._is_authenticated = True
            await self._save_session()

            logger.info("Login successful")
            return True

        except TwoFactorRequired:
            # Re-raise 2FA exception for caller to handle
            raise

        except Exception as e:
            logger.error(f"Login failed: {e}")
            await self.browser.take_screenshot(page, "login_error")
            raise AuthenticationError(f"Login failed: {e}") from e

        finally:
            if own_page:
                await page.close()

    async def _fill_login_field(
        self,
        page: Page,
        primary_selector: str,
        alt_selector: str,
        value: str,
        field_name: str,
    ) -> None:
        """Fill a login form field, trying alternative selector if needed."""
        try:
            if await self.browser.element_exists(page, primary_selector):
                await self.browser.human_type(page, primary_selector, value)
            elif await self.browser.element_exists(page, alt_selector):
                await self.browser.human_type(page, alt_selector, value)
            else:
                raise AuthenticationError(f"Could not find {field_name} input field")
        except Exception as e:
            raise AuthenticationError(f"Failed to fill {field_name}: {e}") from e

    async def _check_login_result(self, page: Page) -> None:
        """Check the result of login attempt."""
        current_url = page.url

        # Success: redirected to feed
        if "feed" in current_url:
            return

        # Check for 2FA / security verification
        if await self.browser.element_exists(page, Selectors.login.VERIFICATION_PROMPT):
            logger.warning("Two-factor authentication required")
            await self.browser.take_screenshot(page, "2fa_required")
            raise TwoFactorRequired(
                "Two-factor authentication is required. "
                "Please complete verification manually and try again."
            )

        # Check for CAPTCHA
        if await self.browser.element_exists(page, Selectors.login.CAPTCHA_CHALLENGE):
            logger.warning("CAPTCHA challenge detected")
            await self.browser.take_screenshot(page, "captcha_required")
            raise AuthenticationError(
                "CAPTCHA challenge detected. Please try again later or use a different network."
            )

        # Check for login errors
        if await self.browser.element_exists(page, Selectors.login.LOGIN_ERROR):
            error_text = await self.browser.get_text(page, Selectors.login.LOGIN_ERROR)
            raise AuthenticationError(f"Login error: {error_text}")

        # Check if still on login page (something went wrong)
        if "login" in current_url or "checkpoint" in current_url:
            await self.browser.take_screenshot(page, "login_unexpected")
            raise AuthenticationError(
                "Login did not complete as expected. Check screenshot for details."
            )

    async def restore_session(self, page: Optional[Page] = None) -> bool:
        """
        Attempt to restore a previous session from saved cookies.

        Args:
            page: Optional page to verify session on

        Returns:
            True if session was restored and is valid
        """
        logger.info("Attempting to restore previous session...")

        # Check if session files exist
        if not self._cookie_path.exists():
            logger.info("No saved session found")
            return False

        # Check session age
        if not self._is_session_valid():
            logger.info("Saved session is too old, need fresh login")
            return False

        # Load cookies
        if not await self.browser.load_cookies(self._cookie_path):
            logger.warning("Failed to load session cookies")
            return False

        # Verify session is still valid by checking LinkedIn
        if page:
            is_valid = await self._verify_session(page)
        else:
            # Create a temporary page to verify
            temp_page = await self.browser.new_page()
            try:
                is_valid = await self._verify_session(temp_page)
            finally:
                await temp_page.close()

        if is_valid:
            self._is_authenticated = True
            logger.info("Session restored successfully")
            return True
        else:
            logger.info("Saved session is no longer valid")
            self._clear_session()
            return False

    async def _verify_session(self, page: Page) -> bool:
        """
        Verify that the current session is valid.

        Args:
            page: Page to use for verification

        Returns:
            True if session is valid
        """
        try:
            # Navigate to LinkedIn feed
            await self.browser.goto(page, Selectors.FEED_URL)
            await self.browser.random_delay(2.0, 3.0)

            # Check if we're on the feed (authenticated) or redirected to login
            current_url = page.url

            if "feed" in current_url:
                # Additional check: look for navigation elements
                has_nav = await self.browser.element_exists(
                    page, Selectors.login.GLOBAL_NAV
                )
                return has_nav

            return False

        except Exception as e:
            logger.warning(f"Session verification failed: {e}")
            return False

    def _is_session_valid(self) -> bool:
        """Check if the saved session is within valid age."""
        if not self._meta_path.exists():
            return False

        try:
            with open(self._meta_path, encoding="utf-8") as f:
                meta = json.load(f)

            saved_at_str = meta.get("saved_at", "")
            # Handle both timezone-aware and naive datetime strings
            saved_at = datetime.fromisoformat(saved_at_str)
            if saved_at.tzinfo is None:
                saved_at = saved_at.replace(tzinfo=timezone.utc)

            max_age = timedelta(days=self.SESSION_MAX_AGE_DAYS)
            now = datetime.now(timezone.utc)

            return now - saved_at < max_age

        except Exception:
            return False

    async def _save_session(self) -> None:
        """Save the current session cookies and metadata."""
        try:
            # Save cookies
            await self.browser.save_cookies(self._cookie_path)

            # Save metadata with UTC timestamp
            meta = {
                "saved_at": datetime.now(timezone.utc).isoformat(),
                "version": "1.0",
            }
            with open(self._meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            logger.info("Session saved successfully")

        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    def _clear_session(self) -> None:
        """Clear saved session data."""
        try:
            if self._cookie_path.exists():
                self._cookie_path.unlink()
            if self._meta_path.exists():
                self._meta_path.unlink()
            logger.info("Session data cleared")
        except Exception as e:
            logger.warning(f"Failed to clear session: {e}")

    async def logout(self, page: Optional[Page] = None) -> None:
        """
        Logout from LinkedIn and clear session.

        Args:
            page: Page to use for logout
        """
        logger.info("Logging out...")

        self._is_authenticated = False
        self._clear_session()

        # Optionally navigate to logout URL
        if page:
            try:
                await self.browser.goto(
                    page,
                    "https://www.linkedin.com/m/logout/",
                    wait_until="load",
                )
            except Exception as e:
                logger.warning(f"Logout navigation failed: {e}")

        logger.info("Logged out successfully")

    async def ensure_authenticated(self, page: Page) -> bool:
        """
        Ensure we have a valid authenticated session.

        Tries to restore session first, then prompts for login if needed.

        Args:
            page: Page to use

        Returns:
            True if authenticated
        """
        if self._is_authenticated:
            return True

        # Try to restore session
        if await self.restore_session(page):
            return True

        # Need fresh login - get credentials from environment
        email = os.getenv("LINKEDIN_EMAIL")
        password = os.getenv("LINKEDIN_PASSWORD")

        if not email or not password:
            logger.error("No saved session and no credentials provided")
            return False

        try:
            return await self.login(email, password, page)
        except TwoFactorRequired:
            logger.error("2FA required - manual intervention needed")
            return False
        except AuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            return False
