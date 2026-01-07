"""Easy Apply form automation for LinkedIn job applications."""

import logging
import random
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout

from ..models.job import Job, JobStatus
from ..models.application import Application, ApplicationStatus
from ..resume.profile import UserProfile
from .job_matcher import JobMatcher


logger = logging.getLogger(__name__)


class ApplicationError(Exception):
    """Custom exception for application errors."""

    pass


class EasyApplyBot:
    """Automates Easy Apply form submission on LinkedIn."""

    def __init__(
        self,
        page: Page,
        profile: UserProfile,
        matcher: JobMatcher,
        min_delay: int = 30,
        max_delay: int = 90,
    ):
        """Initialize Easy Apply bot.

        Args:
            page: Playwright page object (must be logged into LinkedIn)
            profile: User profile for form filling
            matcher: JobMatcher for answering custom questions
            min_delay: Minimum delay between applications (seconds)
            max_delay: Maximum delay between applications (seconds)
        """
        self.page = page
        self.profile = profile
        self.matcher = matcher
        self.min_delay = min_delay
        self.max_delay = max_delay

        logger.info("EasyApplyBot initialized")

    def apply_to_job(self, job: Job) -> Application:
        """Apply to a job using Easy Apply.

        Args:
            job: Job to apply to

        Returns:
            Application record

        Raises:
            ApplicationError: If application fails
        """
        logger.info(f"Starting application to {job.title} at {job.company}")

        application = Application(
            job_id=job.linkedin_job_id,
            status=ApplicationStatus.PENDING,
        )

        try:
            # Navigate to job page
            self._navigate_to_job(job)

            # Click Easy Apply button
            self._click_easy_apply()

            # Fill out application form(s)
            custom_responses = self._fill_application_forms()
            application.custom_questions = custom_responses

            # Submit application
            self._submit_application()

            # Mark as submitted
            application.status = ApplicationStatus.SUBMITTED
            application.submitted_at = datetime.now(timezone.utc)
            job.status = JobStatus.APPLIED
            job.applied_at = datetime.now(timezone.utc)

            logger.info(f"[SUCCESS] Applied to {job.title} at {job.company}")

            # Human-like delay before next application
            self._random_delay()

            return application

        except Exception as e:
            logger.error(f"Failed to apply to {job.title}: {e}")
            application.notes = f"Application failed: {str(e)}"
            raise ApplicationError(f"Failed to apply: {str(e)}")

    def _navigate_to_job(self, job: Job) -> None:
        """Navigate to job posting page.

        Args:
            job: Job to navigate to
        """
        if job.application_url:
            url = job.application_url
        else:
            url = f"https://www.linkedin.com/jobs/view/{job.linkedin_job_id}"

        logger.debug(f"Navigating to {url}")

        try:
            self.page.goto(url, timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=10000)
        except PlaywrightTimeout:
            logger.warning("Page load timeout, continuing anyway")

    def _click_easy_apply(self) -> None:
        """Click the Easy Apply button.

        Raises:
            ApplicationError: If Easy Apply button not found
        """
        logger.debug("Looking for Easy Apply button")

        # Common selectors for Easy Apply button
        selectors = [
            'button:has-text("Easy Apply")',
            'button.jobs-apply-button',
            'button[aria-label*="Easy Apply"]',
        ]

        for selector in selectors:
            try:
                button = self.page.wait_for_selector(selector, timeout=5000)
                if button:
                    button.click()
                    logger.debug("Clicked Easy Apply button")
                    time.sleep(2)  # Wait for modal to open
                    return
            except PlaywrightTimeout:
                continue

        raise ApplicationError("Easy Apply button not found")

    def _fill_application_forms(self) -> Dict[str, str]:
        """Fill out all pages of Easy Apply form.

        Returns:
            Dictionary of custom questions and answers

        Raises:
            ApplicationError: If form filling fails
        """
        logger.debug("Filling application forms")

        custom_responses = {}
        max_pages = 10  # Safety limit
        page_count = 0

        while page_count < max_pages:
            page_count += 1
            logger.debug(f"Processing form page {page_count}")

            # Fill current page
            page_responses = self._fill_current_page()
            custom_responses.update(page_responses)

            # Check if this is the last page
            if self._is_final_page():
                logger.debug("Reached final page")
                break

            # Click Next button
            if not self._click_next():
                logger.debug("No Next button found, assuming last page")
                break

            time.sleep(1)

        if page_count >= max_pages:
            raise ApplicationError("Too many form pages, possible infinite loop")

        return custom_responses

    def _fill_current_page(self) -> Dict[str, str]:
        """Fill out fields on current form page.

        Returns:
            Dictionary of custom question responses
        """
        responses = {}

        # Fill standard fields
        self._fill_standard_fields()

        # Handle custom questions
        custom_questions = self._find_custom_questions()

        for question_element, question_text in custom_questions:
            answer = self._answer_custom_question(question_text)
            responses[question_text] = answer

            # Fill in the answer
            self._fill_question_field(question_element, answer)

        return responses

    def _fill_standard_fields(self) -> None:
        """Fill standard form fields (name, email, phone)."""
        # Phone number
        phone_selectors = [
            'input[id*="phone"]',
            'input[name*="phone"]',
            'input[aria-label*="phone"]',
        ]

        for selector in phone_selectors:
            try:
                field = self.page.query_selector(selector)
                if field and self.profile.phone:
                    # Clear and fill
                    field.fill("")
                    field.type(self.profile.phone, delay=100)
                    logger.debug("Filled phone number")
                    break
            except Exception as e:
                logger.debug(f"Error filling phone: {e}")

    def _find_custom_questions(self) -> list[tuple[Any, str]]:
        """Find custom questions on the form.

        Returns:
            List of (element, question_text) tuples
        """
        questions = []

        # Look for text areas and their labels
        text_areas = self.page.query_selector_all("textarea")

        for textarea in text_areas:
            # Try to find associated label
            label = None

            # Method 1: aria-label
            aria_label = textarea.get_attribute("aria-label")
            if aria_label:
                label = aria_label

            # Method 2: associated label element
            if not label:
                textarea_id = textarea.get_attribute("id")
                if textarea_id:
                    label_elem = self.page.query_selector(f'label[for="{textarea_id}"]')
                    if label_elem:
                        label = label_elem.inner_text()

            # Method 3: parent label
            if not label:
                try:
                    label_elem = textarea.query_selector("xpath=ancestor::label")
                    if label_elem:
                        label = label_elem.inner_text()
                except Exception:
                    pass

            if label:
                questions.append((textarea, label.strip()))
                logger.debug(f"Found custom question: {label.strip()[:50]}...")

        return questions

    def _answer_custom_question(self, question: str) -> str:
        """Generate answer to custom question using JobMatcher.

        Args:
            question: The question to answer

        Returns:
            Generated answer
        """
        logger.debug(f"Generating answer for: {question[:50]}...")

        answer = self.matcher.answer_application_question(question)

        if not answer:
            # Fallback to generic response
            answer = "I am very interested in this opportunity and believe my experience would be a great fit."
            logger.warning("Using fallback answer")

        return answer

    def _fill_question_field(self, element: Any, answer: str) -> None:
        """Fill a question field with an answer.

        Args:
            element: Form element
            answer: Answer text
        """
        try:
            element.fill("")
            element.type(answer, delay=50)  # Human-like typing speed
            logger.debug(f"Filled answer ({len(answer)} chars)")
        except Exception as e:
            logger.error(f"Error filling field: {e}")

    def _is_final_page(self) -> bool:
        """Check if current page is the final review page.

        Returns:
            True if this is the final page
        """
        # Look for Review or Submit button
        review_selectors = [
            'button:has-text("Review")',
            'button:has-text("Submit application")',
            'button[aria-label*="Submit"]',
        ]

        for selector in review_selectors:
            try:
                element = self.page.query_selector(selector)
                if element:
                    return True
            except Exception:
                continue

        return False

    def _click_next(self) -> bool:
        """Click Next button to go to next form page.

        Returns:
            True if Next button was clicked
        """
        next_selectors = [
            'button:has-text("Next")',
            'button[aria-label="Continue to next step"]',
            'button.artdeco-button--primary:has-text("Continue")',
        ]

        for selector in next_selectors:
            try:
                button = self.page.query_selector(selector)
                if button and button.is_visible() and button.is_enabled():
                    button.click()
                    time.sleep(2)  # Wait for page to load
                    return True
            except Exception as e:
                logger.debug(f"Error clicking next: {e}")
                continue

        return False

    def _submit_application(self) -> None:
        """Submit the application.

        Raises:
            ApplicationError: If submission fails
        """
        logger.debug("Submitting application")

        submit_selectors = [
            'button:has-text("Submit application")',
            'button[aria-label*="Submit application"]',
            'button.artdeco-button--primary:has-text("Submit")',
        ]

        for selector in submit_selectors:
            try:
                button = self.page.wait_for_selector(selector, timeout=5000)
                if button and button.is_enabled():
                    button.click()
                    logger.info("Clicked submit button")

                    # Wait for confirmation
                    time.sleep(3)

                    # Check for success message
                    if self._check_submission_success():
                        return
            except PlaywrightTimeout:
                continue
            except Exception as e:
                logger.error(f"Error submitting: {e}")
                continue

        raise ApplicationError("Could not submit application")

    def _check_submission_success(self) -> bool:
        """Check if application was submitted successfully.

        Returns:
            True if submission successful
        """
        success_indicators = [
            'h3:has-text("Application sent")',
            'text="Your application was sent"',
            'text="Application submitted"',
        ]

        for indicator in success_indicators:
            try:
                element = self.page.query_selector(indicator)
                if element:
                    logger.info("Application submission confirmed")
                    return True
            except Exception:
                continue

        return False

    def _random_delay(self) -> None:
        """Random delay to mimic human behavior."""
        delay = random.randint(self.min_delay, self.max_delay)
        logger.debug(f"Waiting {delay} seconds before next action")
        time.sleep(delay)
