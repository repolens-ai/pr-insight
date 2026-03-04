from unittest.mock import MagicMock, patch

import pytest

from pr_insight.tools.pr_config import PRConfig


class TestPRConfig:
    """Test suite for PR Config tool."""

    @pytest.fixture
    def mock_git_provider(self):
        provider = MagicMock()
        provider.get_pr_branch.return_value = "feature-branch"
        provider.pr.title = "Test PR"
        provider.get_user_id.return_value = "user123"
        return provider

    @pytest.fixture
    def mock_settings(self):
        with patch('pr_insight.tools.pr_config.get_settings') as mock:
            yield mock

    def test_pr_config_initialization(self, mock_git_provider, mock_settings):
        """Test PRConfig initialization."""
        mock_settings.return_value = MagicMock()
        
        with patch('pr_insight.tools.pr_config.get_git_provider', return_value=lambda url: mock_git_provider):
            config = PRConfig(pr_url="https://github.com/owner/repo/pull/1")
            assert config.git_provider is not None

    def test_pr_config_run(self, mock_git_provider, mock_settings):
        """Test PRConfig run method."""
        mock_settings.return_value = MagicMock()
        
        with patch('pr_insight.tools.pr_config.get_git_provider', return_value=lambda url: mock_git_provider):
            config = PRConfig(pr_url="https://github.com/owner/repo/pull/1")
            config.run()
