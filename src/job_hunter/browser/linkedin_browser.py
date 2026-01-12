"""
LinkedIn browser automation with stealth mode and human-like behavior.

Provides a Playwright-based browser wrapper with anti-detection features
and utilities for interacting with LinkedIn.
"""

import asyncio
import logging
import platform
import random
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)
from playwright_stealth import stealth_async

# Detect platform for keyboard shortcuts
IS_MAC = platform.system() == "Darwin"
MODIFIER_KEY = "Meta" if IS_MAC else "Control"

logger = logging.getLogger(__name__)


class LinkedInBrowser:
    """
    Browser wrapper for LinkedIn automation with stealth features.

    Features:
    - Stealth mode to avoid bot detection
    - Human-like mouse movements and typing
    - Configurable random delays
    - Screenshot capture for debugging
    - Graceful error handling

    Usage:
        async with LinkedInBrowser() as browser:
            page = await browser.new_page()
            await browser.goto(page, "https://www.linkedin.com")
    """

    # Common user agents to rotate (updated for 2025/2026)
    USER_AGENTS = [
        # Chrome 131+ (Windows)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        # Chrome 131+ (Mac)
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        # Firefox 133+ (Windows)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
        # Safari 18+ (Mac)
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
        # Edge 131+ (Windows)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    ]

    # Common viewport sizes
    VIEWPORT_SIZES = [
        {"width": 1920, "height": 1080},
        {"width": 1366, "height": 768},
        {"width": 1536, "height": 864},
        {"width": 1440, "height": 900},
        {"width": 1280, "height": 720},
    ]

    def __init__(
        self,
        headless: bool = False,
        min_delay: float = 30.0,
        max_delay: float = 90.0,
        slow_mo: int = 50,
        screenshots_dir: Optional[Path] = None,
    ):
        """
        Initialize the LinkedIn browser.

        Args:
            headless: Run browser in headless mode (default: False for debugging)
            min_delay: Minimum delay between major actions in seconds
            max_delay: Maximum delay between major actions in seconds
            slow_mo: Slowdown browser actions by this many ms (helps avoid detection)
            screenshots_dir: Directory to save debug screenshots
        """
        self.headless = headless
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.slow_mo = slow_mo
        self.screenshots_dir = screenshots_dir or Path("data/screenshots")

        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

        # Ensure screenshots directory exists
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

    async def __aenter__(self) -> "LinkedInBrowser":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def start(self) -> None:
        """Start the browser with stealth settings."""
        logger.info("Starting browser with stealth mode...")

        self._playwright = await async_playwright().start()

        # Launch browser with anti-detection settings
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )

        # Create context with randomized fingerprint
        viewport = random.choice(self.VIEWPORT_SIZES)
        user_agent = random.choice(self.USER_AGENTS)

        self._context = await self._browser.new_context(
            viewport=viewport,
            user_agent=user_agent,
            locale="en-US",
            timezone_id="America/New_York",
            geolocation={"latitude": 40.7128, "longitude": -74.0060},  # NYC
            permissions=["geolocation"],
            color_scheme="light",
            device_scale_factor=1,
        )

        # Set extra HTTP headers
        await self._context.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        })

        logger.info(f"Browser started with viewport {viewport['width']}x{viewport['height']}")

    async def close(self) -> None:
        """Close the browser and clean up resources."""
        logger.info("Closing browser...")

        if self._context:
            await self._context.close()
            self._context = None

        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

        logger.info("Browser closed")

    async def new_page(self) -> Page:
        """
        Create a new page with stealth mode enabled.

        Returns:
            A new Page instance with stealth applied
        """
        if not self._context:
            raise RuntimeError("Browser not started. Call start() first.")

        page = await self._context.new_page()

        # Apply stealth to avoid detection
        await stealth_async(page)

        # Add custom JavaScript to mask automation
        await page.add_init_script("""
            // Override navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });

            // Override navigator.plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });

            // Override navigator.languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });

            // Override chrome runtime
            window.chrome = {
                runtime: {},
            };
        """)

        return page

    async def goto(
        self,
        page: Page,
        url: str,
        wait_until: str = "domcontentloaded",
        timeout: int = 30000,
    ) -> None:
        """
        Navigate to a URL with human-like behavior.

        Args:
            page: Playwright page instance
            url: URL to navigate to
            wait_until: Wait condition (load, domcontentloaded, networkidle)
            timeout: Navigation timeout in milliseconds
        """
        logger.debug(f"Navigating to {url}")

        await page.goto(url, wait_until=wait_until, timeout=timeout)

        # Random small delay after navigation
        await self.random_delay(0.5, 2.0)

    async def random_delay(
        self,
        min_seconds: Optional[float] = None,
        max_seconds: Optional[float] = None,
    ) -> None:
        """
        Wait for a random amount of time (human-like behavior).

        Args:
            min_seconds: Minimum wait time (uses instance default if None)
            max_seconds: Maximum wait time (uses instance default if None)
        """
        min_s = min_seconds if min_seconds is not None else self.min_delay
        max_s = max_seconds if max_seconds is not None else self.max_delay

        delay = random.uniform(min_s, max_s)
        logger.debug(f"Waiting {delay:.2f} seconds...")
        await asyncio.sleep(delay)

    async def human_type(
        self,
        page: Page,
        selector: str,
        text: str,
        clear_first: bool = True,
    ) -> None:
        """
        Type text with human-like delays between keystrokes.

        Args:
            page: Playwright page instance
            selector: CSS selector for the input element
            text: Text to type
            clear_first: Clear existing text before typing
        """
        element = await page.wait_for_selector(selector, timeout=10000)

        if clear_first:
            await element.click()
            # Use platform-appropriate modifier key (Cmd on Mac, Ctrl on Windows/Linux)
            await page.keyboard.press(f"{MODIFIER_KEY}+a")
            await asyncio.sleep(random.uniform(0.1, 0.3))
            await page.keyboard.press("Backspace")
            await asyncio.sleep(random.uniform(0.2, 0.5))

        # Type with random delays between characters
        for char in text:
            await element.type(char, delay=random.randint(50, 150))

        await asyncio.sleep(random.uniform(0.2, 0.5))

    async def human_click(
        self,
        page: Page,
        selector: str,
        timeout: int = 10000,
    ) -> None:
        """
        Click an element with human-like behavior.

        Args:
            page: Playwright page instance
            selector: CSS selector for the element to click
            timeout: Wait timeout in milliseconds
        """
        element = await page.wait_for_selector(selector, timeout=timeout)

        # Get element bounding box for random click position
        box = await element.bounding_box()

        if box:
            # Click at a random position within the element
            x = box["x"] + random.uniform(box["width"] * 0.2, box["width"] * 0.8)
            y = box["y"] + random.uniform(box["height"] * 0.2, box["height"] * 0.8)

            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.3))
            await page.mouse.click(x, y)
        else:
            # Fallback to regular click
            await element.click()

        await asyncio.sleep(random.uniform(0.3, 0.7))

    async def scroll_page(
        self,
        page: Page,
        direction: str = "down",
        amount: int = 300,
    ) -> None:
        """
        Scroll the page with human-like behavior.

        Args:
            page: Playwright page instance
            direction: Scroll direction ('up' or 'down')
            amount: Pixels to scroll
        """
        delta = amount if direction == "down" else -amount

        # Add some randomness to scroll amount
        delta = int(delta * random.uniform(0.8, 1.2))

        await page.mouse.wheel(0, delta)
        await asyncio.sleep(random.uniform(0.3, 0.8))

    async def scroll_to_element(
        self,
        page: Page,
        selector: str,
        timeout: int = 10000,
    ) -> None:
        """
        Scroll to make an element visible.

        Args:
            page: Playwright page instance
            selector: CSS selector for the target element
            timeout: Wait timeout in milliseconds
        """
        element = await page.wait_for_selector(selector, timeout=timeout)
        await element.scroll_into_view_if_needed()
        await asyncio.sleep(random.uniform(0.3, 0.7))

    async def wait_for_element(
        self,
        page: Page,
        selector: str,
        timeout: int = 10000,
        state: str = "visible",
    ) -> bool:
        """
        Wait for an element to appear.

        Args:
            page: Playwright page instance
            selector: CSS selector for the element
            timeout: Wait timeout in milliseconds
            state: Element state to wait for (visible, hidden, attached, detached)

        Returns:
            True if element found, False otherwise
        """
        try:
            await page.wait_for_selector(selector, timeout=timeout, state=state)
            return True
        except Exception:
            return False

    async def element_exists(
        self,
        page: Page,
        selector: str,
    ) -> bool:
        """
        Check if an element exists on the page.

        Args:
            page: Playwright page instance
            selector: CSS selector for the element

        Returns:
            True if element exists, False otherwise
        """
        element = await page.query_selector(selector)
        return element is not None

    async def get_text(
        self,
        page: Page,
        selector: str,
        default: str = "",
    ) -> str:
        """
        Get text content of an element.

        Args:
            page: Playwright page instance
            selector: CSS selector for the element
            default: Default value if element not found

        Returns:
            Element text content or default value
        """
        try:
            element = await page.query_selector(selector)
            if element:
                text = await element.text_content()
                return text.strip() if text else default
            return default
        except Exception:
            return default

    async def get_attribute(
        self,
        page: Page,
        selector: str,
        attribute: str,
        default: str = "",
    ) -> str:
        """
        Get an attribute value from an element.

        Args:
            page: Playwright page instance
            selector: CSS selector for the element
            attribute: Attribute name to get
            default: Default value if not found

        Returns:
            Attribute value or default
        """
        try:
            element = await page.query_selector(selector)
            if element:
                value = await element.get_attribute(attribute)
                return value if value else default
            return default
        except Exception:
            return default

    async def take_screenshot(
        self,
        page: Page,
        name: str,
    ) -> Path:
        """
        Take a screenshot for debugging.

        Args:
            page: Playwright page instance
            name: Screenshot name (without extension)

        Returns:
            Path to the saved screenshot
        """
        filename = f"{name}.png"
        filepath = self.screenshots_dir / filename

        await page.screenshot(path=str(filepath), full_page=False)
        logger.debug(f"Screenshot saved: {filepath}")

        return filepath

    async def save_cookies(self, filepath: Path) -> None:
        """
        Save browser cookies to a file.

        Args:
            filepath: Path to save cookies JSON
        """
        if not self._context:
            raise RuntimeError("Browser not started")

        import json

        cookies = await self._context.cookies()
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w") as f:
            json.dump(cookies, f, indent=2)

        logger.info(f"Cookies saved to {filepath}")

    async def load_cookies(self, filepath: Path) -> bool:
        """
        Load cookies from a file.

        Args:
            filepath: Path to cookies JSON file

        Returns:
            True if cookies loaded successfully, False otherwise
        """
        if not self._context:
            raise RuntimeError("Browser not started")

        import json

        if not filepath.exists():
            logger.warning(f"Cookie file not found: {filepath}")
            return False

        try:
            with open(filepath) as f:
                cookies = json.load(f)

            await self._context.add_cookies(cookies)
            logger.info(f"Cookies loaded from {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return False

    @property
    def context(self) -> Optional[BrowserContext]:
        """Get the browser context."""
        return self._context

    @property
    def browser(self) -> Optional[Browser]:
        """Get the browser instance."""
        return self._browser


@asynccontextmanager
async def create_browser(
    headless: bool = False,
    min_delay: float = 30.0,
    max_delay: float = 90.0,
    **kwargs,
) -> AsyncGenerator[LinkedInBrowser, None]:
    """
    Convenience function to create a browser with context manager.

    Args:
        headless: Run in headless mode
        min_delay: Minimum delay between actions
        max_delay: Maximum delay between actions
        **kwargs: Additional arguments for LinkedInBrowser

    Yields:
        LinkedInBrowser instance
    """
    browser = LinkedInBrowser(
        headless=headless,
        min_delay=min_delay,
        max_delay=max_delay,
        **kwargs,
    )
    try:
        await browser.start()
        yield browser
    finally:
        await browser.close()
