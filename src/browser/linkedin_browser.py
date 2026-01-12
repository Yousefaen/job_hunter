"""LinkedIn browser automation with stealth mode."""

import logging
import os
import random
import time
from pathlib import Path
from typing import Optional

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright, Playwright

logger = logging.getLogger(__name__)


class LinkedInBrowser:
    """Browser wrapper with stealth mode for LinkedIn automation."""

    def __init__(
        self,
        headless: bool = False,
        user_data_dir: Optional[str] = None,
        slow_mo: int = 50,
    ):
        """Initialize LinkedIn browser.

        Args:
            headless: Run in headless mode (not recommended for LinkedIn)
            user_data_dir: Directory to persist browser session
            slow_mo: Slow down operations by this many milliseconds
        """
        self.headless = headless
        self.slow_mo = slow_mo

        # Default user data directory for session persistence
        if user_data_dir:
            self.user_data_dir = Path(user_data_dir)
        else:
            self.user_data_dir = Path.home() / ".job_hunter" / "browser_data"

        self.user_data_dir.mkdir(parents=True, exist_ok=True)

        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

        logger.info(f"LinkedInBrowser initialized (headless={headless})")

    def start(self) -> Page:
        """Start browser and return the page.

        Returns:
            Playwright Page object
        """
        logger.info("Starting browser...")

        self._playwright = sync_playwright().start()

        # Use chromium with stealth settings
        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )

        # Create context with stealth settings
        self._context = self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=self._get_user_agent(),
            locale="en-US",
            timezone_id="America/New_York",
            permissions=["geolocation"],
            geolocation={"latitude": 40.7128, "longitude": -74.0060},  # NYC
            color_scheme="light",
        )

        # Add stealth scripts
        self._add_stealth_scripts()

        # Create page
        self._page = self._context.new_page()

        # Set extra headers
        self._page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
        })

        logger.info("Browser started successfully")
        return self._page

    def _get_user_agent(self) -> str:
        """Get a realistic user agent string."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        ]
        return random.choice(user_agents)

    def _add_stealth_scripts(self) -> None:
        """Add stealth JavaScript to avoid detection."""
        if not self._context:
            return

        stealth_js = """
        // Override webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        // Override plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });

        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });

        // Override chrome property
        window.chrome = {
            runtime: {}
        };

        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        """

        self._context.add_init_script(stealth_js)
        logger.debug("Stealth scripts added")

    @property
    def page(self) -> Optional[Page]:
        """Get the current page."""
        return self._page

    @property
    def context(self) -> Optional[BrowserContext]:
        """Get the browser context."""
        return self._context

    def save_cookies(self, filepath: Optional[str] = None) -> None:
        """Save cookies for session persistence.

        Args:
            filepath: Path to save cookies (default: user_data_dir/cookies.json)
        """
        if not self._context:
            logger.warning("No context to save cookies from")
            return

        if filepath is None:
            filepath = str(self.user_data_dir / "cookies.json")

        cookies = self._context.cookies()

        import json
        with open(filepath, 'w') as f:
            json.dump(cookies, f, indent=2)

        logger.info(f"Saved {len(cookies)} cookies to {filepath}")

    def load_cookies(self, filepath: Optional[str] = None) -> bool:
        """Load cookies from file.

        Args:
            filepath: Path to load cookies from

        Returns:
            True if cookies were loaded successfully
        """
        if not self._context:
            logger.warning("No context to load cookies into")
            return False

        if filepath is None:
            filepath = str(self.user_data_dir / "cookies.json")

        if not os.path.exists(filepath):
            logger.debug(f"No cookie file found at {filepath}")
            return False

        import json
        try:
            with open(filepath, 'r') as f:
                cookies = json.load(f)

            self._context.add_cookies(cookies)
            logger.info(f"Loaded {len(cookies)} cookies from {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return False

    def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
        """Random delay to mimic human behavior.

        Args:
            min_seconds: Minimum delay
            max_seconds: Maximum delay
        """
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def human_type(self, selector: str, text: str, clear_first: bool = True) -> None:
        """Type text with human-like delays.

        Args:
            selector: Element selector
            text: Text to type
            clear_first: Clear the field first
        """
        if not self._page:
            return

        element = self._page.locator(selector)

        if clear_first:
            element.clear()

        # Type with random delays between characters
        for char in text:
            element.type(char, delay=random.randint(50, 150))

    def human_click(self, selector: str) -> None:
        """Click with human-like behavior.

        Args:
            selector: Element selector
        """
        if not self._page:
            return

        element = self._page.locator(selector)

        # Move to element first
        element.hover()
        self.random_delay(0.2, 0.5)

        # Click
        element.click()

    def scroll_page(self, direction: str = "down", amount: int = 300) -> None:
        """Scroll the page.

        Args:
            direction: "up" or "down"
            amount: Pixels to scroll
        """
        if not self._page:
            return

        if direction == "down":
            self._page.mouse.wheel(0, amount)
        else:
            self._page.mouse.wheel(0, -amount)

        self.random_delay(0.3, 0.8)

    def close(self) -> None:
        """Close browser and cleanup resources."""
        logger.info("Closing browser...")

        if self._page:
            try:
                self._page.close()
            except Exception:
                pass
            self._page = None

        if self._context:
            try:
                self._context.close()
            except Exception:
                pass
            self._context = None

        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

        logger.info("Browser closed")

    def __enter__(self) -> "LinkedInBrowser":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def screenshot(self, path: str) -> None:
        """Take a screenshot.

        Args:
            path: Path to save screenshot
        """
        if self._page:
            self._page.screenshot(path=path)
            logger.debug(f"Screenshot saved to {path}")
