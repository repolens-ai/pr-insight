from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pr_insight.tools.pr_generate_labels import PRGenerateLabels


class TestPRGenerateLabels:
    """Test suite for PR Generate Labels tool."""

    @pytest.fixture
    def mock_git_provider(self):
        provider = MagicMock()
        provider.get_pr_branch.return_value = "feature-branch"
        provider.pr.title = "Test PR"
        provider.get_pr_description.return_value = "Test description"
        provider.get_languages.return_value = {"Python": 80, "JavaScript": 20}
        provider.get_files.return_value = ["test.py", "test.js"]
        return provider

    @pytest.fixture
    def mock_ai_handler(self):
        handler = MagicMock()
        handler.chat_completion = AsyncMock(return_value=("bug, feature", "stop"))
        return handler

    @pytest.fixture
    def mock_settings(self):
        with patch('pr_insight.tools.pr_generate_labels.get_settings') as mock:
            mock.return_value.pr_generate_labels = MagicMock()
            mock.return_value.pr_generate_labels.extra_instructions = ""
            mock.return_value.pr_generate_labels_prompt = MagicMock()
            mock.return_value.pr_generate_labels_prompt.system = "System prompt"
            mock.return_value.pr_generate_labels_prompt.user = "User prompt"
            mock.return_value.config = MagicMock()
            mock.return_value.config.temperature = 0.2
            yield mock

    def test_initialization(self, mock_git_provider, mock_ai_handler, mock_settings):
        """Test PRGenerateLabels initialization."""
        with patch('pr_insight.tools.pr_generate_labels.get_git_provider', return_value=lambda url: mock_git_provider):
            with patch('pr_insight.tools.pr_generate_labels.get_main_pr_language', return_value="Python"):
                labels = PRGenerateLabels(
                    pr_url="https://github.com/owner/repo/pull/1",
                    ai_handler=lambda: mock_ai_handler
                )
                assert labels.git_provider is not None
