"""Job search functionality for LinkedIn."""

import logging
import random
import re
import time
from datetime import datetime, timezone
from typing import Optional, Generator
from urllib.parse import urlencode, quote_plus

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout

from ..browser.selectors import Selectors
from ..models.job import Job
from ..models.search_criteria import SearchCriteria

logger = logging.getLogger(__name__)


class JobSearcher:
    """Searches for jobs on LinkedIn and extracts job details."""

    JOBS_URL = "https://www.linkedin.com/jobs/search/"

    def __init__(
        self,
        page: Page,
        criteria: SearchCriteria,
        min_delay: float = 2.0,
        max_delay: float = 5.0,
    ):
        """Initialize job searcher.

        Args:
            page: Playwright page object (must be logged in)
            criteria: Search criteria to apply
            min_delay: Minimum delay between actions (seconds)
            max_delay: Maximum delay between actions (seconds)
        """
        self.page = page
        self.criteria = criteria
        self.min_delay = min_delay
        self.max_delay = max_delay
        self._jobs_found: list[Job] = []

        logger.info("JobSearcher initialized")

    def _random_delay(self, min_override: Optional[float] = None, max_override: Optional[float] = None) -> None:
        """Random delay to mimic human behavior."""
        min_d = min_override if min_override is not None else self.min_delay
        max_d = max_override if max_override is not None else self.max_delay
        delay = random.uniform(min_d, max_d)
        time.sleep(delay)

    def build_search_url(self, title: str, location: str) -> str:
        """Build LinkedIn job search URL with filters.

        Args:
            title: Job title to search
            location: Location to search in

        Returns:
            Formatted search URL
        """
        params = {
            "keywords": title,
            "location": location,
            "refresh": "true",
        }

        # Add date posted filter
        date_mapping = {
            "Past 24 hours": "r86400",
            "Past week": "r604800",
            "Past month": "r2592000",
        }
        if self.criteria.date_posted in date_mapping:
            params["f_TPR"] = date_mapping[self.criteria.date_posted]

        # Add Easy Apply filter
        if self.criteria.easy_apply_only:
            params["f_AL"] = "true"

        # Add experience level filter
        exp_mapping = {
            "Entry level": "2",
            "Associate": "3",
            "Mid-Senior level": "4",
            "Director": "5",
            "Executive": "6",
        }
        if self.criteria.experience_levels:
            exp_values = [exp_mapping[e] for e in self.criteria.experience_levels if e in exp_mapping]
            if exp_values:
                params["f_E"] = ",".join(exp_values)

        # Add company size filter
        size_mapping = {
            "1-10 employees": "B",
            "11-50 employees": "C",
            "51-200 employees": "D",
            "201-500 employees": "E",
            "501-1000 employees": "F",
            "1001-5000 employees": "G",
            "5001-10000 employees": "H",
            "10001+ employees": "I",
        }
        if self.criteria.company_sizes:
            size_values = [size_mapping[s] for s in self.criteria.company_sizes if s in size_mapping]
            if size_values:
                params["f_CS"] = ",".join(size_values)

        url = f"{self.JOBS_URL}?{urlencode(params)}"
        logger.debug(f"Built search URL: {url}")
        return url

    def search(self, max_results: int = 50) -> list[Job]:
        """Search for jobs based on criteria.

        Args:
            max_results: Maximum number of jobs to return

        Returns:
            List of Job objects
        """
        logger.info(f"Starting job search (max {max_results} results)")
        all_jobs: list[Job] = []

        # Search for each title/location combination
        for title in self.criteria.titles:
            for location in self.criteria.locations:
                if len(all_jobs) >= max_results:
                    break

                logger.info(f"Searching: {title} in {location}")
                jobs = self._search_title_location(
                    title,
                    location,
                    max_results - len(all_jobs)
                )
                all_jobs.extend(jobs)

                self._random_delay(3, 6)

        logger.info(f"Search complete. Found {len(all_jobs)} jobs")
        self._jobs_found = all_jobs
        return all_jobs

    def _search_title_location(self, title: str, location: str, max_results: int) -> list[Job]:
        """Search for a specific title and location.

        Args:
            title: Job title
            location: Location
            max_results: Maximum results for this search

        Returns:
            List of jobs found
        """
        jobs: list[Job] = []

        # Navigate to search URL
        search_url = self.build_search_url(title, location)

        try:
            self.page.goto(search_url, timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)
        except PlaywrightTimeout:
            logger.warning("Page load timeout, continuing anyway")

        self._random_delay(2, 4)

        # Scroll to load more results
        page_num = 1
        max_pages = 5

        while len(jobs) < max_results and page_num <= max_pages:
            logger.debug(f"Processing page {page_num}")

            # Extract jobs from current view
            new_jobs = self._extract_jobs_from_page()

            for job in new_jobs:
                if len(jobs) >= max_results:
                    break

                # Skip if we already have this job
                if any(j.id == job.id for j in jobs):
                    continue

                # Apply basic filters
                if self._passes_basic_filters(job):
                    jobs.append(job)
                    logger.debug(f"Found: {job.title} at {job.company}")

            # Try to go to next page
            if not self._go_to_next_page():
                break

            page_num += 1
            self._random_delay(2, 4)

        return jobs

    def _extract_jobs_from_page(self) -> list[Job]:
        """Extract job listings from current page.

        Returns:
            List of Job objects
        """
        jobs: list[Job] = []

        # Try different selectors for job cards
        job_cards = None
        for selector in Selectors.get_job_card_selectors():
            try:
                cards = self.page.query_selector_all(selector)
                if cards:
                    job_cards = cards
                    break
            except Exception:
                continue

        if not job_cards:
            logger.warning("No job cards found on page")
            return jobs

        logger.debug(f"Found {len(job_cards)} job cards")

        for card in job_cards:
            try:
                job = self._extract_job_from_card(card)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.debug(f"Error extracting job from card: {e}")
                continue

        return jobs

    def _extract_job_from_card(self, card) -> Optional[Job]:
        """Extract job details from a job card element.

        Args:
            card: Job card element

        Returns:
            Job object or None
        """
        try:
            # Get job ID from data attribute or link
            job_id = card.get_attribute("data-job-id")
            if not job_id:
                link = card.query_selector("a[href*='/jobs/view/']")
                if link:
                    href = link.get_attribute("href")
                    match = re.search(r'/jobs/view/(\d+)', href)
                    if match:
                        job_id = match.group(1)

            if not job_id:
                return None

            # Extract title
            title_elem = card.query_selector(Selectors.JOB_CARD_TITLE) or \
                         card.query_selector(Selectors.JOB_TITLE_ALT) or \
                         card.query_selector("a[class*='title']")
            title = title_elem.inner_text().strip() if title_elem else "Unknown"

            # Extract company
            company_elem = card.query_selector(Selectors.JOB_CARD_COMPANY) or \
                           card.query_selector(Selectors.JOB_COMPANY_ALT) or \
                           card.query_selector("[class*='company']")
            company = company_elem.inner_text().strip() if company_elem else "Unknown"

            # Extract location
            location_elem = card.query_selector(Selectors.JOB_CARD_LOCATION) or \
                            card.query_selector(Selectors.JOB_LOCATION_ALT) or \
                            card.query_selector("[class*='location']")
            location = location_elem.inner_text().strip() if location_elem else "Unknown"

            # Check for Easy Apply
            easy_apply = bool(card.query_selector(Selectors.JOB_CARD_EASY_APPLY)) or \
                         bool(card.query_selector('[class*="easy-apply"]'))

            return Job(
                id=job_id,
                title=title,
                company=company,
                location=location,
                description="",  # Will be filled when viewing details
                url=f"https://www.linkedin.com/jobs/view/{job_id}",
                easy_apply=easy_apply,
            )

        except Exception as e:
            logger.debug(f"Error extracting job: {e}")
            return None

    def get_job_details(self, job: Job) -> Job:
        """Get full job details by viewing the job page.

        Args:
            job: Job to get details for

        Returns:
            Updated Job with full details
        """
        logger.debug(f"Getting details for: {job.title} at {job.company}")

        # Click on job card to show details panel, or navigate to job page
        job_url = job.url or f"https://www.linkedin.com/jobs/view/{job.id}"

        try:
            self.page.goto(job_url, timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=10000)
        except PlaywrightTimeout:
            logger.warning("Page load timeout, continuing anyway")

        self._random_delay(1, 2)

        # Extract description
        desc_selectors = [
            Selectors.JOB_DETAIL_DESCRIPTION,
            Selectors.JOB_DESC_ALT,
            Selectors.JOB_DESC_CONTENT,
            ".jobs-description",
            "#job-details",
        ]

        for selector in desc_selectors:
            try:
                desc_elem = self.page.query_selector(selector)
                if desc_elem:
                    job.description = desc_elem.inner_text().strip()
                    break
            except Exception:
                continue

        # Try to extract company size from job insights
        try:
            insights = self.page.query_selector_all(Selectors.JOB_DETAIL_CRITERIA)
            for insight in insights:
                text = insight.inner_text().lower()
                if "employees" in text:
                    # Extract company size
                    size_match = re.search(r'(\d+(?:,\d+)?(?:-\d+(?:,\d+)?)?)\s*employees', text)
                    if size_match:
                        job.company_size = size_match.group(0)
        except Exception:
            pass

        # Verify Easy Apply status
        for selector in Selectors.get_easy_apply_selectors():
            try:
                easy_apply_btn = self.page.query_selector(selector)
                if easy_apply_btn and easy_apply_btn.is_visible():
                    job.easy_apply = True
                    break
            except Exception:
                continue

        logger.debug(f"Got details: {len(job.description)} chars description")
        return job

    def _passes_basic_filters(self, job: Job) -> bool:
        """Check if job passes basic filters.

        Args:
            job: Job to check

        Returns:
            True if job passes filters
        """
        # Check excluded locations
        for excluded in self.criteria.excluded_locations:
            if excluded.lower() in job.location.lower():
                logger.debug(f"Filtered out: {job.title} - excluded location")
                return False

        # Check excluded companies
        if self.criteria.is_company_excluded(job.company):
            logger.debug(f"Filtered out: {job.title} - excluded company")
            return False

        # Check excluded keywords in title
        title_lower = job.title.lower()
        for keyword in self.criteria.excluded_keywords:
            if keyword.lower() in title_lower:
                logger.debug(f"Filtered out: {job.title} - excluded keyword")
                return False

        # Check Easy Apply if required
        if self.criteria.easy_apply_only and not job.easy_apply:
            logger.debug(f"Filtered out: {job.title} - not Easy Apply")
            return False

        return True

    def _go_to_next_page(self) -> bool:
        """Navigate to next page of results.

        Returns:
            True if navigation successful
        """
        try:
            # First try scrolling to load more (infinite scroll)
            self.page.mouse.wheel(0, 500)
            self._random_delay(1, 2)

            # Try pagination button
            next_button = self.page.query_selector(Selectors.PAGINATION_NEXT)
            if next_button and next_button.is_visible() and next_button.is_enabled():
                next_button.click()
                self._random_delay(2, 3)
                return True

            # Try numbered page buttons
            current_page = self.page.query_selector('button[aria-current="true"]')
            if current_page:
                current_num = int(current_page.inner_text())
                next_page_btn = self.page.query_selector(f'button[aria-label="Page {current_num + 1}"]')
                if next_page_btn and next_page_btn.is_visible():
                    next_page_btn.click()
                    self._random_delay(2, 3)
                    return True

            return False

        except Exception as e:
            logger.debug(f"Error navigating to next page: {e}")
            return False

    def search_and_get_details(self, max_results: int = 25) -> Generator[Job, None, None]:
        """Search for jobs and yield each with full details.

        This is a generator that yields jobs one at a time with full details.
        Useful for processing jobs as they're found.

        Args:
            max_results: Maximum number of jobs

        Yields:
            Job objects with full details
        """
        # First, get basic job listings
        jobs = self.search(max_results)

        # Then get details for each
        for job in jobs:
            try:
                detailed_job = self.get_job_details(job)
                yield detailed_job
            except Exception as e:
                logger.error(f"Error getting details for {job.title}: {e}")
                yield job  # Yield without details

            self._random_delay(2, 4)
