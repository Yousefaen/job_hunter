"""Tests for job matching functionality."""

from unittest.mock import Mock, patch

import pytest

from src.agent.job_matcher import JobMatcher, MatchResult
from src.models.job import Job, JobStatus
from src.models.search_criteria import SearchCriteria
from src.resume.profile import UserProfile


class TestJobMatcher:
    """Tests for JobMatcher class."""

    def test_init_without_api_key(self, sample_profile, sample_criteria, monkeypatch):
        """Test initialization fails without API key."""
        # Clear env var to ensure test isolation
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ValueError, match="API key required"):
            JobMatcher(sample_profile, sample_criteria, api_key=None)

    def test_init_with_api_key(self, sample_profile, sample_criteria):
        """Test successful initialization with API key."""
        matcher = JobMatcher(
            sample_profile,
            sample_criteria,
            api_key="sk-ant-test-key"
        )

        assert matcher.profile == sample_profile
        assert matcher.criteria == sample_criteria
        assert len(matcher.profile_keywords) > 0

    def test_keyword_filter_excluded_location(
        self,
        sample_profile,
        sample_criteria,
        excluded_location_job,
    ):
        """Test keyword filter rejects excluded locations."""
        matcher = JobMatcher(
            sample_profile,
            sample_criteria,
            api_key="sk-ant-test-key"
        )

        result = matcher.keyword_filter(excluded_location_job)
        assert result is False

    def test_keyword_filter_wrong_company_size(
        self,
        sample_profile,
        sample_criteria,
        poor_match_job,
    ):
        """Test keyword filter rejects wrong company size."""
        matcher = JobMatcher(
            sample_profile,
            sample_criteria,
            api_key="sk-ant-test-key"
        )

        result = matcher.keyword_filter(poor_match_job)
        assert result is False

    def test_keyword_filter_good_match(
        self,
        sample_profile,
        sample_criteria,
        good_match_job,
    ):
        """Test keyword filter accepts good matches."""
        matcher = JobMatcher(
            sample_profile,
            sample_criteria,
            api_key="sk-ant-test-key"
        )

        result = matcher.keyword_filter(good_match_job)
        assert result is True

    def test_keyword_filter_insufficient_keywords(
        self,
        sample_profile,
        sample_criteria,
    ):
        """Test keyword filter rejects jobs with too few keyword matches."""
        matcher = JobMatcher(
            sample_profile,
            sample_criteria,
            api_key="sk-ant-test-key"
        )

        # Job with only 1 keyword match
        job = Job(
            linkedin_job_id="11111",
            title="Unrelated Position",
            company="Random Corp",
            location="New York, NY",
            description="This is a completely unrelated job.",
            company_size="11-50 employees",
        )

        result = matcher.keyword_filter(job)
        assert result is False

    @patch("src.agent.job_matcher.Anthropic")
    def test_score_job_match_success(
        self,
        mock_anthropic,
        sample_profile,
        sample_criteria,
        good_match_job,
    ):
        """Test successful job scoring."""
        # Mock Claude API response
        mock_message = Mock()
        mock_message.content = [
            Mock(
                text='{"score": 85, "reasoning": "Great fit", '
                '"key_matches": ["Chief of Staff", "OKRs"], '
                '"concerns": []}'
            )
        ]
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        matcher = JobMatcher(
            sample_profile,
            sample_criteria,
            api_key="sk-ant-test-key"
        )

        result = matcher.score_job_match(good_match_job)

        assert isinstance(result, MatchResult)
        assert result.score == 85
        assert result.is_match is True
        assert "Great fit" in result.reasoning
        assert len(result.key_matches) == 2

    @patch("src.agent.job_matcher.Anthropic")
    def test_score_job_match_low_score(
        self,
        mock_anthropic,
        sample_profile,
        sample_criteria,
        poor_match_job,
    ):
        """Test job scoring with low score."""
        # Mock Claude API response with low score
        mock_message = Mock()
        mock_message.content = [
            Mock(
                text='{"score": 25, "reasoning": "Not a good fit", '
                '"key_matches": [], '
                '"concerns": ["Wrong role", "Different industry"]}'
            )
        ]
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        matcher = JobMatcher(
            sample_profile,
            sample_criteria,
            api_key="sk-ant-test-key"
        )

        result = matcher.score_job_match(poor_match_job)

        assert result.score == 25
        assert result.is_match is False
        assert len(result.concerns) == 2

    @patch("src.agent.job_matcher.Anthropic")
    def test_score_job_match_api_error(
        self,
        mock_anthropic,
        sample_profile,
        sample_criteria,
        good_match_job,
    ):
        """Test job scoring handles API errors gracefully."""
        # Mock API error
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic.return_value = mock_client

        matcher = JobMatcher(
            sample_profile,
            sample_criteria,
            api_key="sk-ant-test-key"
        )

        result = matcher.score_job_match(good_match_job)

        assert result.score == 0
        assert result.is_match is False
        assert "Error" in result.reasoning

    @patch("src.agent.job_matcher.Anthropic")
    def test_answer_application_question(
        self,
        mock_anthropic,
        sample_profile,
        sample_criteria,
    ):
        """Test answering application questions."""
        # Mock Claude API response
        mock_message = Mock()
        mock_message.content = [
            Mock(
                text="I have extensive experience leading cross-functional teams "
                "and implementing strategic initiatives at early-stage startups."
            )
        ]
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        matcher = JobMatcher(
            sample_profile,
            sample_criteria,
            api_key="sk-ant-test-key"
        )

        question = "Why are you interested in this Chief of Staff role?"
        answer = matcher.answer_application_question(question)

        assert len(answer) > 0
        assert "experience" in answer.lower()

    @patch("src.agent.job_matcher.Anthropic")
    def test_match_job_full_pipeline_match(
        self,
        mock_anthropic,
        sample_profile,
        sample_criteria,
        good_match_job,
    ):
        """Test complete matching pipeline for a matching job."""
        # Mock Claude API response
        mock_message = Mock()
        mock_message.content = [
            Mock(
                text='{"score": 85, "reasoning": "Great fit", '
                '"key_matches": ["Chief of Staff"], '
                '"concerns": []}'
            )
        ]
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        matcher = JobMatcher(
            sample_profile,
            sample_criteria,
            api_key="sk-ant-test-key"
        )

        updated_job, is_match = matcher.match_job(good_match_job)

        assert is_match is True
        assert updated_job.status == JobStatus.MATCHED
        assert updated_job.match_score == 85
        assert updated_job.match_reasoning is not None

    @patch("src.agent.job_matcher.Anthropic")
    def test_match_job_full_pipeline_reject(
        self,
        mock_anthropic,
        sample_profile,
        sample_criteria,
        poor_match_job,
    ):
        """Test complete matching pipeline for a non-matching job."""
        matcher = JobMatcher(
            sample_profile,
            sample_criteria,
            api_key="sk-ant-test-key"
        )

        # This job should be rejected by keyword filter
        updated_job, is_match = matcher.match_job(poor_match_job)

        assert is_match is False
        assert updated_job.status == JobStatus.REJECTED

    def test_parse_scoring_response_valid_json(
        self,
        sample_profile,
        sample_criteria,
    ):
        """Test parsing valid JSON response."""
        matcher = JobMatcher(
            sample_profile,
            sample_criteria,
            api_key="sk-ant-test-key"
        )

        response = '{"score": 75, "reasoning": "Good match", "key_matches": [], "concerns": []}'
        result = matcher._parse_scoring_response(response)

        assert result["score"] == 75
        assert result["reasoning"] == "Good match"

    def test_parse_scoring_response_json_with_text(
        self,
        sample_profile,
        sample_criteria,
    ):
        """Test parsing JSON embedded in text."""
        matcher = JobMatcher(
            sample_profile,
            sample_criteria,
            api_key="sk-ant-test-key"
        )

        response = 'Here is my analysis: {"score": 65, "reasoning": "Decent fit"} That concludes my review.'
        result = matcher._parse_scoring_response(response)

        assert result["score"] == 65

    def test_parse_scoring_response_invalid_json(
        self,
        sample_profile,
        sample_criteria,
    ):
        """Test parsing handles invalid JSON gracefully."""
        matcher = JobMatcher(
            sample_profile,
            sample_criteria,
            api_key="sk-ant-test-key"
        )

        response = "This is not JSON at all"
        result = matcher._parse_scoring_response(response)

        assert result["score"] == 0
        assert "Failed to parse" in result["reasoning"]

    def test_parse_scoring_response_score_out_of_range(
        self,
        sample_profile,
        sample_criteria,
    ):
        """Test parsing clamps scores to 0-100 range."""
        matcher = JobMatcher(
            sample_profile,
            sample_criteria,
            api_key="sk-ant-test-key"
        )

        # Score too high
        response = '{"score": 150, "reasoning": "Perfect!"}'
        result = matcher._parse_scoring_response(response)
        assert result["score"] == 100

        # Score too low
        response = '{"score": -20, "reasoning": "Terrible"}'
        result = matcher._parse_scoring_response(response)
        assert result["score"] == 0


class TestMatchResult:
    """Tests for MatchResult model."""

    def test_match_result_creation(self):
        """Test creating a MatchResult."""
        result = MatchResult(
            score=85,
            reasoning="Strong alignment with role requirements",
            key_matches=["Strategic planning", "OKRs"],
            concerns=["Limited startup experience"],
            is_match=True,
        )

        assert result.score == 85
        assert result.is_match is True
        assert len(result.key_matches) == 2
        assert len(result.concerns) == 1

    def test_match_result_defaults(self):
        """Test MatchResult with default values."""
        result = MatchResult(
            score=50,
            reasoning="Average fit",
        )

        assert result.key_matches == []
        assert result.concerns == []
        assert result.is_match is False


class TestSearchCriteria:
    """Tests for SearchCriteria model."""

    def test_search_criteria_defaults(self):
        """Test SearchCriteria with default values."""
        criteria = SearchCriteria()

        assert criteria.min_match_score == 60
        assert criteria.max_applications_per_day == 25
        assert criteria.min_delay_between_applications == 30
        assert criteria.max_delay_between_applications == 90
        assert "Israel" in criteria.excluded_locations

    def test_search_criteria_custom_values(self):
        """Test SearchCriteria with custom values."""
        criteria = SearchCriteria(
            min_match_score=70,
            max_applications_per_day=10,
            min_delay_between_applications=60,
            max_delay_between_applications=120,
        )

        assert criteria.min_match_score == 70
        assert criteria.max_applications_per_day == 10
        assert criteria.min_delay_between_applications == 60
        assert criteria.max_delay_between_applications == 120

    def test_search_criteria_invalid_delay_order(self):
        """Test SearchCriteria rejects max_delay < min_delay."""
        with pytest.raises(ValueError, match="max_delay.*must be >= min_delay"):
            SearchCriteria(
                min_delay_between_applications=100,
                max_delay_between_applications=50,
            )

    def test_search_criteria_equal_delays_valid(self):
        """Test SearchCriteria accepts equal min and max delays."""
        criteria = SearchCriteria(
            min_delay_between_applications=60,
            max_delay_between_applications=60,
        )

        assert criteria.min_delay_between_applications == 60
        assert criteria.max_delay_between_applications == 60
