"""Job matching logic using keyword filtering and Claude API."""

import json
import logging
import os
from typing import Optional
from pydantic import BaseModel, Field

from anthropic import Anthropic, APIError, RateLimitError, AuthenticationError

from ..models.job import Job, JobStatus
from ..models.search_criteria import SearchCriteria
from ..resume.profile import UserProfile


# Default model for scoring - can be overridden via configuration
DEFAULT_MODEL = "claude-sonnet-4-20250514"


logger = logging.getLogger(__name__)


class MatchResult(BaseModel):
    """Result of job matching analysis."""

    score: int = Field(..., ge=0, le=100)
    reasoning: str
    key_matches: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    is_match: bool = False


class JobMatcher:
    """Matches jobs to user profile using keyword filtering and LLM scoring."""

    def __init__(
        self,
        profile: UserProfile,
        criteria: SearchCriteria,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """Initialize job matcher.

        Args:
            profile: User's resume profile
            criteria: Search criteria and matching thresholds
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use (defaults to DEFAULT_MODEL)
        """
        self.profile = profile
        self.criteria = criteria
        self.model = model or DEFAULT_MODEL

        # Get API key but don't store it as instance variable
        resolved_api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        if not resolved_api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable."
            )

        self.client = Anthropic(api_key=resolved_api_key)
        self.profile_keywords = profile.get_keywords()

        logger.info(f"JobMatcher initialized with {len(self.profile_keywords)} keywords")

    def keyword_filter(self, job: Job) -> bool:
        """Fast keyword-based filtering before LLM scoring.

        Args:
            job: Job to filter

        Returns:
            True if job passes keyword filter
        """
        job_text = f"{job.title} {job.description} {job.company}".lower()

        # Check excluded locations
        for excluded_loc in self.criteria.excluded_locations:
            if excluded_loc.lower() in job.location.lower():
                logger.debug(f"Filtered out {job.title} - excluded location: {excluded_loc}")
                return False

        # Check company size if available
        if job.company_size and self.criteria.company_sizes:
            if job.company_size not in self.criteria.company_sizes:
                logger.debug(f"Filtered out {job.title} - company size: {job.company_size}")
                return False

        # Check excluded keywords
        for keyword in self.criteria.excluded_keywords:
            if keyword.lower() in job_text:
                logger.debug(f"Filtered out {job.title} - excluded keyword: {keyword}")
                return False

        # Check required keywords (if specified)
        if self.criteria.required_keywords:
            has_required = any(
                keyword.lower() in job_text
                for keyword in self.criteria.required_keywords
            )
            if not has_required:
                logger.debug(f"Filtered out {job.title} - missing required keywords")
                return False

        # Check for any profile keyword matches (basic relevance)
        keyword_matches = sum(
            1 for keyword in self.profile_keywords
            if keyword in job_text
        )

        # Require at least 2 keyword matches for relevance
        if keyword_matches < 2:
            logger.debug(f"Filtered out {job.title} - insufficient keyword matches ({keyword_matches})")
            return False

        logger.debug(f"Passed keyword filter: {job.title} ({keyword_matches} matches)")
        return True

    def score_job_match(self, job: Job) -> MatchResult:
        """Score job-resume fit using Claude API.

        Args:
            job: Job to score

        Returns:
            MatchResult with score and reasoning
        """
        logger.info(f"Scoring job match: {job.title} at {job.company}")

        # Prepare prompt for Claude
        prompt = self._build_scoring_prompt(job)

        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,  # Lower temperature for consistent scoring
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            # Parse response
            response_text = response.content[0].text

            # Extract JSON from response
            match_data = self._parse_scoring_response(response_text)

            # Create MatchResult
            result = MatchResult(
                score=match_data.get("score", 0),
                reasoning=match_data.get("reasoning", ""),
                key_matches=match_data.get("key_matches", []),
                concerns=match_data.get("concerns", []),
                is_match=match_data.get("score", 0) >= self.criteria.min_match_score,
            )

            logger.info(
                f"Match score for {job.title}: {result.score}/100 "
                f"({'MATCH' if result.is_match else 'NO MATCH'})"
            )

            return result

        except AuthenticationError as e:
            logger.error(f"Authentication error - check API key: {e}")
            raise  # Re-raise auth errors - they're not recoverable
        except RateLimitError as e:
            logger.warning(f"Rate limit hit for job {job.title}: {e}")
            # Return low score but don't raise - caller can retry later
            return MatchResult(
                score=0,
                reasoning="Rate limit hit - please retry later",
                concerns=["Rate limit error"],
                is_match=False,
            )
        except APIError as e:
            logger.error(f"API error scoring job {job.title}: {e}")
            return MatchResult(
                score=0,
                reasoning=f"API error during scoring: {str(e)}",
                is_match=False,
            )
        except Exception as e:
            logger.error(f"Unexpected error scoring job {job.title}: {e}")
            return MatchResult(
                score=0,
                reasoning=f"Error during scoring: {str(e)}",
                is_match=False,
            )

    def _build_scoring_prompt(self, job: Job) -> str:
        """Build prompt for job scoring.

        Args:
            job: Job to score

        Returns:
            Formatted prompt
        """
        profile_summary = self.profile.get_summary_text()

        prompt = f"""You are a career matching expert. Score how well this candidate fits this job posting on a scale of 0-100.

CANDIDATE PROFILE:
{profile_summary}

JOB POSTING:
Title: {job.title}
Company: {job.company}
Location: {job.location}
{f'Company Size: {job.company_size}' if job.company_size else ''}
{f'Experience Level: {job.experience_level}' if job.experience_level else ''}

Description:
{job.description}

SCORING CRITERIA:
- Role alignment: Does this match Chief of Staff / BizOps / Business Operations focus?
- Skills match: How well do candidate's skills align with job requirements?
- Experience fit: Is the experience level appropriate (mid to senior)?
- Company stage fit: Is this likely a Seed to Series A startup (based on company size and description)?
- Location fit: Does location match candidate preferences?

Return your analysis as JSON with this structure:
{{
  "score": <0-100>,
  "reasoning": "<2-3 sentence explanation of the score>",
  "key_matches": ["<strength 1>", "<strength 2>", ...],
  "concerns": ["<potential gap 1>", "<potential gap 2>", ...]
}}

Be honest and rigorous in your scoring. A score of 60+ indicates a good match worth applying to.
"""
        return prompt

    def _parse_scoring_response(self, response_text: str) -> dict:
        """Parse Claude's scoring response.

        Args:
            response_text: Raw response from Claude

        Returns:
            Parsed JSON data
        """
        try:
            # Try to find JSON in the response
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")

            json_str = response_text[start_idx:end_idx]
            data = json.loads(json_str)

            # Validate required fields
            if "score" not in data:
                raise ValueError("Missing 'score' field in response")

            # Ensure score is in valid range
            data["score"] = max(0, min(100, int(data["score"])))

            return data

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse scoring response: {e}")
            logger.debug(f"Response text: {response_text}")

            # Return default low score
            return {
                "score": 0,
                "reasoning": "Failed to parse matching score",
                "key_matches": [],
                "concerns": ["Unable to analyze match quality"],
            }

    def answer_application_question(
        self,
        question: str,
        context: Optional[str] = None,
    ) -> str:
        """Generate answer to application question using Claude API.

        Args:
            question: The application question to answer
            context: Additional context about the question

        Returns:
            Generated answer
        """
        logger.info(f"Generating answer for question: {question[:50]}...")

        prompt = self._build_question_prompt(question, context)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.7,  # Slightly higher for more natural responses
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            answer = response.content[0].text.strip()
            logger.info(f"Generated answer ({len(answer)} chars)")

            return answer

        except AuthenticationError:
            logger.error("Authentication error - check API key")
            raise  # Re-raise auth errors
        except RateLimitError as e:
            logger.warning(f"Rate limit hit generating answer: {e}")
            return ""  # Return empty, caller should handle fallback
        except APIError as e:
            logger.error(f"API error generating answer: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error generating answer: {e}")
            return ""

    def _build_question_prompt(self, question: str, context: Optional[str]) -> str:
        """Build prompt for answering application questions.

        Args:
            question: The question to answer
            context: Additional context

        Returns:
            Formatted prompt
        """
        profile_summary = self.profile.get_summary_text()

        prompt = f"""You are helping a candidate answer a job application question. Provide a concise, professional answer based on their background.

CANDIDATE BACKGROUND:
{profile_summary}

APPLICATION QUESTION:
{question}

{f'ADDITIONAL CONTEXT:\n{context}\n' if context else ''}

Provide a concise, professional answer (2-4 sentences) that:
- Draws from actual experience and skills in the candidate's background
- Is honest and authentic
- Matches the professional tone appropriate for Chief of Staff / Business Operations roles
- Is specific and avoids generic platitudes

Return ONLY the answer text, without any preamble or explanation.
"""
        return prompt

    def match_job(self, job: Job) -> tuple[Job, bool]:
        """Complete matching pipeline for a job.

        Args:
            job: Job to match

        Returns:
            Tuple of (updated Job, matched boolean)
        """
        # Step 1: Keyword filter
        if not self.keyword_filter(job):
            job.status = JobStatus.REJECTED
            logger.debug(f"Job rejected by keyword filter: {job.title}")
            return job, False

        job.status = JobStatus.FILTERED

        # Step 2: LLM scoring
        match_result = self.score_job_match(job)

        # Update job with match results
        job.match_score = match_result.score
        job.match_reasoning = match_result.reasoning
        job.key_matches = match_result.key_matches
        job.concerns = match_result.concerns

        if match_result.is_match:
            job.status = JobStatus.MATCHED
            logger.info(f"[MATCHED] {job.title} at {job.company} (score: {match_result.score})")
            return job, True
        else:
            job.status = JobStatus.REJECTED
            logger.info(f"[REJECTED] {job.title} at {job.company} (score: {match_result.score})")
            return job, False
