from unittest.mock import MagicMock, patch
import pytest

from pr_insight.tools.pr_reviewer import PRReviewer


class TestPRReviewer:
    """Test suite for PR Reviewer tool."""

    @pytest.fixture
    def mock_git_provider(self):
        provider = MagicMock()
        provider.get_pr_branch.return_value = "feature-branch"
        provider.pr.title = "Test PR"
        provider.pr.body = "Test description"
        provider.get_user_id.return_value = "user123"
        provider.get_diff_files.return_value = []
        provider.get_pr_url.return_value = "https://github.com/owner/repo/pull/1"
        provider.get_pr_num.return_value = 1
        provider.is_supported.return_value = True
        provider.get_languages.return_value = {"Python": 100}
        provider.get_files.return_value = {"test.py": "content"}
        provider.get_pr_description.return_value = ("description", [])
        return provider

    def test_pr_reviewer_initialization(self, mock_git_provider):
        """Test PRReviewer initialization."""
        with patch("pr_insight.tools.pr_reviewer.get_git_provider_with_context", return_value=mock_git_provider):
            with patch("pr_insight.tools.pr_reviewer.LiteLLMAIHandler") as mock_handler:
                mock_handler_instance = MagicMock()
                mock_handler.return_value = mock_handler_instance
                reviewer = PRReviewer(pr_url="https://github.com/owner/repo/pull/1")
                assert reviewer.git_provider is not None

    def test_pr_reviewer_args_default_to_none(self, mock_git_provider):
        """Test PRReviewer args default to None."""
        with patch("pr_insight.tools.pr_reviewer.get_git_provider_with_context", return_value=mock_git_provider):
            with patch("pr_insight.tools.pr_reviewer.LiteLLMAIHandler") as mock_handler:
                mock_handler_instance = MagicMock()
                mock_handler.return_value = mock_handler_instance
                reviewer = PRReviewer(pr_url="https://github.com/owner/repo/pull/1")
                assert reviewer.args is None

    def test_pr_reviewer_incremental_property(self, mock_git_provider):
        """Test PRReviewer incremental property exists."""
        with patch("pr_insight.tools.pr_reviewer.get_git_provider_with_context", return_value=mock_git_provider):
            with patch("pr_insight.tools.pr_reviewer.LiteLLMAIHandler") as mock_handler:
                mock_handler_instance = MagicMock()
                mock_handler.return_value = mock_handler_instance
                reviewer = PRReviewer(pr_url="https://github.com/owner/repo/pull/1")
                assert hasattr(reviewer, "incremental")
