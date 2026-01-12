"""
Job search functionality for LinkedIn.

Handles searching for jobs, extracting listings, and parsing job details.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, replace
from datetime import datetime
from typing import TYPE_CHECKING, AsyncGenerator, Optional
from urllib.parse import urlencode

from playwright.async_api import Page

from job_hunter.browser.linkedin_browser import LinkedInBrowser
from job_hunter.browser.selectors import Selectors

if TYPE_CHECKING:
    from job_hunter.models.job import Job
    from job_hunter.models.search_criteria import SearchCriteria

logger = logging.getLogger(__name__)


@dataclass
class JobListing:
    """
    Represents a job listing extracted from LinkedIn.

    This is a lightweight data class for raw extraction.
    Use to_job() to convert to the full Job model after enrichment.
    """

    job_id: str
    title: str
    company: str
    location: str
    url: str
    easy_apply: bool = False
    posted_date: Optional[str] = None
    company_size: Optional[str] = None
    description: Optional[str] = None
    experience_level: Optional[str] = None
    job_type: Optional[str] = None

    def to_job(self) -> "Job":
        """
        Convert this JobListing to a full Job model.

        Returns:
            Job model instance with all available fields populated.

        Raises:
            ImportError: If the job_hunter.models module is not available.
        """
        from job_hunter.models.job import Job

        return Job(
            job_id=self.job_id,
            title=self.title,
            company=self.company,
            location=self.location,
            description=self.description or "",
            url=self.url,
            easy_apply=self.easy_apply,
            posted_date=self.posted_date,
            company_size=self.company_size,
            experience_level=self.experience_level,
            job_type=self.job_type,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    def with_details(
        self,
        description: Optional[str] = None,
        company_size: Optional[str] = None,
        experience_level: Optional[str] = None,
        job_type: Optional[str] = None,
        easy_apply: Optional[bool] = None,
    ) -> "JobListing":
        """
        Return a new JobListing with updated details (immutable update pattern).

        Args:
            description: Job description text
            company_size: Company size (e.g., "11-50 employees")
            experience_level: Required experience level
            job_type: Job type (e.g., "Full-time")
            easy_apply: Whether Easy Apply is available

        Returns:
            New JobListing instance with updated fields
        """
        return replace(
            self,
            description=description if description is not None else self.description,
            company_size=company_size if company_size is not None else self.company_size,
            experience_level=experience_level if experience_level is not None else self.experience_level,
            job_type=job_type if job_type is not None else self.job_type,
            easy_apply=easy_apply if easy_apply is not None else self.easy_apply,
        )


class JobSearchError(Exception):
    """Raised when job search fails."""
    pass


class NoResultsError(JobSearchError):
    """Raised when search returns no results."""
    pass


class JobSearcher:
    """
    Searches for jobs on LinkedIn and extracts listing data.

    Features:
    - Search with filters (title, location, experience level, etc.)
    - Easy Apply filtering
    - Pagination handling
    - Job detail extraction
    - Company size detection

    Usage:
        searcher = JobSearcher(browser)
        async for job in searcher.search_jobs(page, criteria):
            print(job.title, job.company)
    """

    # LinkedIn filter values mapping
    DATE_POSTED_FILTERS = {
        "Past 24 hours": "r86400",
        "Past week": "r604800",
        "Past month": "r2592000",
        "Any time": "",
    }

    EXPERIENCE_LEVEL_FILTERS = {
        "Internship": "1",
        "Entry level": "2",
        "Associate": "3",
        "Mid-Senior level": "4",
        "Senior level": "4",  # LinkedIn uses same value as Mid-Senior
        "Director": "5",
        "Executive": "6",
    }

    JOB_TYPE_FILTERS = {
        "Full-time": "F",
        "Part-time": "P",
        "Contract": "C",
        "Temporary": "T",
        "Volunteer": "V",
        "Internship": "I",
    }

    def __init__(self, browser: LinkedInBrowser):
        """
        Initialize the job searcher.

        Args:
            browser: LinkedInBrowser instance
        """
        self.browser = browser

    def build_search_url(
        self,
        keywords: str,
        location: str,
        date_posted: Optional[str] = None,
        experience_levels: Optional[list[str]] = None,
        job_types: Optional[list[str]] = None,
        easy_apply_only: bool = True,
        start: int = 0,
    ) -> str:
        """
        Build a LinkedIn job search URL with filters.

        Args:
            keywords: Job title/keywords to search
            location: Location to search in
            date_posted: Date filter (e.g., "Past week")
            experience_levels: List of experience levels
            job_types: List of job types
            easy_apply_only: Only show Easy Apply jobs
            start: Pagination offset

        Returns:
            Complete search URL with parameters
        """
        params = {
            "keywords": keywords,
            "location": location,
            "origin": "JOB_SEARCH_PAGE_SEARCH_BUTTON",
            "refresh": "true",
        }

        # Add date posted filter
        if date_posted and date_posted in self.DATE_POSTED_FILTERS:
            filter_value = self.DATE_POSTED_FILTERS[date_posted]
            if filter_value:
                params["f_TPR"] = filter_value

        # Add experience level filters
        if experience_levels:
            exp_values = [
                self.EXPERIENCE_LEVEL_FILTERS[level]
                for level in experience_levels
                if level in self.EXPERIENCE_LEVEL_FILTERS
            ]
            if exp_values:
                params["f_E"] = ",".join(exp_values)

        # Add job type filters
        if job_types:
            type_values = [
                self.JOB_TYPE_FILTERS[jt]
                for jt in job_types
                if jt in self.JOB_TYPE_FILTERS
            ]
            if type_values:
                params["f_JT"] = ",".join(type_values)

        # Add Easy Apply filter
        if easy_apply_only:
            params["f_AL"] = "true"

        # Add pagination
        if start > 0:
            params["start"] = str(start)

        return f"{Selectors.JOBS_SEARCH_URL}?{urlencode(params)}"

    async def search_jobs(
        self,
        page: Page,
        keywords: str,
        location: str,
        date_posted: Optional[str] = "Past week",
        experience_levels: Optional[list[str]] = None,
        job_types: Optional[list[str]] = None,
        easy_apply_only: bool = True,
        max_results: int = 100,
    ) -> AsyncGenerator[JobListing, None]:
        """
        Search for jobs and yield results.

        Args:
            page: Playwright page instance
            keywords: Job title/keywords to search
            location: Location to search in
            date_posted: Date filter
            experience_levels: Experience level filters
            job_types: Job type filters
            easy_apply_only: Only Easy Apply jobs
            max_results: Maximum number of results to return

        Yields:
            JobListing objects for each found job

        Raises:
            NoResultsError: If no job listings are found on the first page
            JobSearchError: If search fails to load
        """
        logger.info(f"Searching for '{keywords}' in '{location}'")

        start = 0
        results_count = 0
        page_size = 25  # LinkedIn's default page size
        seen_job_ids: set[str] = set()  # Track seen jobs to avoid duplicates
        is_first_page = True

        while results_count < max_results:
            # Build and navigate to search URL
            search_url = self.build_search_url(
                keywords=keywords,
                location=location,
                date_posted=date_posted,
                experience_levels=experience_levels,
                job_types=job_types,
                easy_apply_only=easy_apply_only,
                start=start,
            )

            logger.debug(f"Navigating to search page (offset={start})")
            await self.browser.goto(page, search_url)
            await self.browser.random_delay(2.0, 4.0)

            # Wait for job listings to load
            listings_found = await self._wait_for_listings(page)

            if not listings_found:
                if is_first_page:
                    raise NoResultsError(
                        f"No job listings found for '{keywords}' in '{location}'"
                    )
                logger.info("No more listings container found, ending search")
                break

            # Extract jobs from current page
            jobs_on_page = await self._extract_job_cards(page)

            if not jobs_on_page:
                if is_first_page:
                    raise NoResultsError(
                        f"No job cards found for '{keywords}' in '{location}'"
                    )
                logger.info("No more jobs found, ending search")
                break

            is_first_page = False
            new_jobs_count = 0

            # Yield each job (with deduplication)
            for job in jobs_on_page:
                if results_count >= max_results:
                    break

                # Skip duplicates
                if job.job_id in seen_job_ids:
                    logger.debug(f"Skipping duplicate job {job.job_id}")
                    continue

                seen_job_ids.add(job.job_id)
                yield job
                results_count += 1
                new_jobs_count += 1

            logger.info(
                f"Extracted {new_jobs_count} new jobs from {len(jobs_on_page)} cards "
                f"(total: {results_count}, duplicates skipped: {len(jobs_on_page) - new_jobs_count})"
            )

            # Check if we should continue to next page
            if len(jobs_on_page) < page_size or new_jobs_count == 0:
                logger.info("Reached last page of results or all duplicates")
                break

            # Move to next page
            start += page_size
            await self.browser.random_delay(3.0, 6.0)

        logger.info(f"Search complete. Found {results_count} unique jobs.")

    async def search_jobs_with_criteria(
        self,
        page: Page,
        criteria: "SearchCriteria",
        max_results: int = 100,
    ) -> AsyncGenerator[JobListing, None]:
        """
        Search for jobs using a SearchCriteria object.

        This method applies all filters from SearchCriteria including:
        - Location and company exclusions
        - Required and excluded keywords
        - All search parameters

        Args:
            page: Playwright page instance
            criteria: SearchCriteria object with all filters
            max_results: Maximum number of results to return

        Yields:
            JobListing objects that pass all criteria filters
        """
        # Search for each title in each location
        total_results = 0

        for title in criteria.titles:
            if total_results >= max_results:
                break

            for location in criteria.locations:
                if total_results >= max_results:
                    break

                logger.info(f"Searching for '{title}' in '{location}'")

                try:
                    async for job in self.search_jobs(
                        page=page,
                        keywords=title,
                        location=location,
                        date_posted=criteria.date_posted,
                        experience_levels=criteria.experience_levels,
                        job_types=criteria.job_types,
                        easy_apply_only=criteria.easy_apply_only,
                        max_results=max_results - total_results,
                    ):
                        # Apply exclusion filters
                        if criteria.should_exclude_location(job.location):
                            logger.debug(f"Excluding job {job.job_id}: location excluded")
                            continue

                        if criteria.should_exclude_company(job.company):
                            logger.debug(f"Excluding job {job.job_id}: company excluded")
                            continue

                        # Check keywords if description is available
                        if job.description:
                            if not criteria.has_required_keywords(job.description):
                                logger.debug(f"Excluding job {job.job_id}: missing required keywords")
                                continue

                            if criteria.has_excluded_keywords(job.description):
                                logger.debug(f"Excluding job {job.job_id}: has excluded keywords")
                                continue

                        yield job
                        total_results += 1

                        if total_results >= max_results:
                            break

                except NoResultsError:
                    logger.info(f"No results for '{title}' in '{location}', continuing...")
                    continue

                # Delay between searches
                await self.browser.random_delay(
                    criteria.min_delay_between_actions,
                    criteria.max_delay_between_actions,
                )

        logger.info(f"Criteria search complete. Found {total_results} matching jobs.")

    async def _wait_for_listings(self, page: Page, timeout: int = 15000) -> bool:
        """
        Wait for job listings to load on the page.

        Args:
            page: Playwright page instance
            timeout: Maximum time to wait in milliseconds

        Returns:
            True if listings container found, False otherwise
        """
        # First check for "no results" indicators
        no_results_selectors = [
            Selectors.job_search.NO_RESULTS,
            Selectors.job_search.NO_RESULTS_ALT,
        ]

        for selector in no_results_selectors:
            if await self.browser.element_exists(page, selector):
                logger.info("No results banner detected")
                return False

        # Wait for job listings container
        selectors_to_try = [
            Selectors.job_search.JOBS_LIST_CONTAINER,
            Selectors.job_search.JOBS_LIST_CONTAINER_ALT,
            Selectors.job_search.SCAFFOLD_LIST,
        ]

        for selector in selectors_to_try:
            if await self.browser.wait_for_element(page, selector, timeout=timeout):
                await self.browser.random_delay(0.5, 1.0)
                return True

        logger.warning("Could not find job listings container")
        return False

    async def _extract_job_cards(self, page: Page) -> list[JobListing]:
        """
        Extract job listings from the current page.

        Args:
            page: Page with job search results

        Returns:
            List of JobListing objects
        """
        jobs = []

        # Find all job cards
        card_selectors = [
            Selectors.job_search.JOB_CARD,
            Selectors.job_search.JOB_CARD_ALT,
        ]

        job_cards = []
        for selector in card_selectors:
            cards = await page.query_selector_all(selector)
            if cards:
                job_cards = cards
                break

        logger.debug(f"Found {len(job_cards)} job cards on page")

        for card in job_cards:
            try:
                job = await self._parse_job_card(card)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.warning(f"Failed to parse job card: {e}")
                continue

        return jobs

    async def _parse_job_card(self, card) -> Optional[JobListing]:
        """
        Parse a single job card element.

        Args:
            card: Job card element

        Returns:
            JobListing if successfully parsed, None otherwise
        """
        try:
            # Extract job link and ID
            link_element = await card.query_selector(
                Selectors.job_search.JOB_CARD_LINK
            ) or await card.query_selector("a[href*='/jobs/view/']")

            if not link_element:
                return None

            href = await link_element.get_attribute("href")
            if not href:
                return None

            # Extract job ID from URL
            job_id = self._extract_job_id(href)
            if not job_id:
                return None

            # Build full URL
            url = f"https://www.linkedin.com/jobs/view/{job_id}"

            # Extract title
            title = await self._get_card_text(
                card,
                [
                    Selectors.job_search.JOB_CARD_TITLE,
                    Selectors.job_search.JOB_CARD_TITLE_ALT,
                    "a.job-card-list__title",
                    "strong",
                ],
            )

            # Extract company
            company = await self._get_card_text(
                card,
                [
                    Selectors.job_search.JOB_CARD_COMPANY,
                    Selectors.job_search.JOB_CARD_COMPANY_ALT,
                    "h4.job-card-container__company-name",
                ],
            )

            # Extract location
            location = await self._get_card_text(
                card,
                [
                    Selectors.job_search.JOB_CARD_LOCATION,
                    "span.job-card-container__metadata-wrapper li",
                ],
            )

            # Check for Easy Apply badge
            easy_apply = await self._check_easy_apply(card)

            # Extract posted date if available
            posted_date = await self._get_card_text(
                card,
                ["time", "span.job-card-container__listed-time"],
            )

            if not title or not company:
                logger.debug(f"Skipping job {job_id}: missing title or company")
                return None

            return JobListing(
                job_id=job_id,
                title=title.strip(),
                company=company.strip(),
                location=location.strip() if location else "",
                url=url,
                easy_apply=easy_apply,
                posted_date=posted_date,
            )

        except Exception as e:
            logger.debug(f"Error parsing job card: {e}")
            return None

    async def _get_card_text(self, card, selectors: list[str]) -> str:
        """Try multiple selectors to get text from a card element."""
        for selector in selectors:
            try:
                element = await card.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text and text.strip():
                        return text.strip()
            except Exception:
                continue
        return ""

    async def _check_easy_apply(self, card) -> bool:
        """Check if a job card has Easy Apply badge."""
        selectors = [
            Selectors.job_search.EASY_APPLY_BADGE,
            Selectors.job_search.EASY_APPLY_ICON,
            "li:has-text('Easy Apply')",
            "span:has-text('Easy Apply')",
        ]

        for selector in selectors:
            try:
                element = await card.query_selector(selector)
                if element:
                    return True
            except Exception:
                continue

        return False

    def _extract_job_id(self, url: str) -> Optional[str]:
        """Extract job ID from a LinkedIn job URL."""
        patterns = [
            r"/jobs/view/(\d+)",
            r"currentJobId=(\d+)",
            r"jobId=(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    async def get_job_details(
        self,
        page: Page,
        job: JobListing,
    ) -> JobListing:
        """
        Get full job details by navigating to the job page.

        Args:
            page: Playwright page instance
            job: JobListing with basic info

        Returns:
            New JobListing instance enriched with full details (immutable pattern)
        """
        logger.debug(f"Fetching details for job {job.job_id}")

        try:
            # Navigate to job page
            await self.browser.goto(page, job.url)
            await self.browser.random_delay(1.5, 3.0)

            # Wait for job details to load
            await self.browser.wait_for_element(
                page,
                Selectors.job_detail.DETAIL_CONTAINER,
                timeout=10000,
            )

            # Extract all details
            description = await self._extract_description(page)
            company_size = await self._extract_company_size(page)
            experience_level = await self._extract_insight(page, "experience")
            job_type = await self._extract_insight(page, "job type")
            easy_apply = await self._check_easy_apply_button(page)

            # Return new instance with updated details (immutable)
            return job.with_details(
                description=description,
                company_size=company_size,
                experience_level=experience_level,
                job_type=job_type,
                easy_apply=easy_apply,
            )

        except Exception as e:
            logger.warning(f"Failed to get details for job {job.job_id}: {e}")
            return job

    async def _extract_description(self, page: Page) -> Optional[str]:
        """Extract job description from detail page."""
        selectors = [
            Selectors.job_detail.DESCRIPTION_TEXT,
            Selectors.job_detail.DESCRIPTION_CONTENT,
            "div.jobs-description__content",
        ]

        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    # Try to expand "Show more" if present
                    show_more = await page.query_selector(
                        Selectors.job_detail.SHOW_MORE_BUTTON
                    )
                    if show_more:
                        try:
                            await show_more.click()
                            await self.browser.random_delay(0.3, 0.6)
                        except Exception:
                            pass

                    text = await element.text_content()
                    if text:
                        return text.strip()
            except Exception:
                continue

        return None

    async def _extract_company_size(self, page: Page) -> Optional[str]:
        """Extract company size from job insights."""
        try:
            # Look for company size in job insights
            insights = await page.query_selector_all(
                Selectors.job_detail.JOB_INSIGHTS
            )

            for insight in insights:
                text = await insight.text_content()
                if text and "employees" in text.lower():
                    # Extract the size range (e.g., "11-50 employees")
                    match = re.search(r"(\d+[-–]\d+\s*employees|\d+\+?\s*employees)", text, re.IGNORECASE)
                    if match:
                        return match.group(1).strip()

            return None
        except Exception:
            return None

    async def _extract_insight(self, page: Page, keyword: str) -> Optional[str]:
        """Extract a specific insight by keyword."""
        try:
            insights = await page.query_selector_all(
                Selectors.job_detail.JOB_INSIGHTS
            )

            for insight in insights:
                text = await insight.text_content()
                if text and keyword.lower() in text.lower():
                    return text.strip()

            return None
        except Exception:
            return None

    async def _check_easy_apply_button(self, page: Page) -> bool:
        """Check if Easy Apply button exists on job detail page."""
        selectors = [
            Selectors.job_detail.EASY_APPLY_BUTTON,
            Selectors.job_detail.EASY_APPLY_BUTTON_ALT,
        ]

        for selector in selectors:
            if await self.browser.element_exists(page, selector):
                return True

        return False

    async def click_job_card(self, page: Page, job_id: str) -> bool:
        """
        Click on a job card to view details in the side panel.

        Args:
            page: Page with job search results
            job_id: ID of the job to click

        Returns:
            True if click was successful
        """
        try:
            # Find the job card by ID
            card = await page.query_selector(f"a[href*='/jobs/view/{job_id}']")

            if not card:
                logger.warning(f"Could not find job card for {job_id}")
                return False

            await card.click()
            await self.browser.random_delay(1.0, 2.0)

            return True

        except Exception as e:
            logger.warning(f"Failed to click job card {job_id}: {e}")
            return False
