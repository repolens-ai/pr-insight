from unittest.mock import MagicMock, patch
import pytest

import yaml

from pr_insight.tools.pr_description import PRDescription, sanitize_diagram

KEYS_FIX = ["filename:", "language:", "changes_summary:", "changes_title:", "description:", "title:"]

def _make_instance(prediction_yaml: str):
    """Create a PRDescription instance, bypassing __init__."""
    with patch.object(PRDescription, '__init__', lambda self, *a, **kw: None):
        obj = PRDescription.__new__(PRDescription)
    obj.prediction = prediction_yaml
    obj.keys_fix = KEYS_FIX
    obj.user_description = ""
    return obj


def _mock_settings():
    """Mock get_settings used by _prepare_data."""
    settings = MagicMock()
    settings.pr_description.add_original_user_description = False
    return settings


def _prediction_with_diagram(diagram_value: str) -> str:
    """Build a minimal YAML prediction string that includes changes_diagram."""
    return yaml.dump({
        'title': 'test',
        'description': 'test',
        'changes_diagram': diagram_value,
    })

class TestPRDescriptionDiagram:

    @patch('pr_insight.tools.pr_description.get_settings')
    def test_diagram_not_starting_with_fence_is_removed(self, mock_get_settings):
        mock_get_settings.return_value = _mock_settings()
        obj = _make_instance(_prediction_with_diagram('graph LR\nA --> B'))
        obj._prepare_data()
        assert 'changes_diagram' not in obj.data

    @patch('pr_insight.tools.pr_description.get_settings')
    def test_diagram_missing_closing_fence_is_appended(self, mock_get_settings):
        mock_get_settings.return_value = _mock_settings()
        obj = _make_instance(_prediction_with_diagram('```mermaid\ngraph LR\nA --> B'))
        obj._prepare_data()
        assert obj.data['changes_diagram'] == '\n```mermaid\ngraph LR\nA --> B\n```'

    @patch('pr_insight.tools.pr_description.get_settings')
    def test_backticks_inside_label_are_removed(self, mock_get_settings):
        mock_get_settings.return_value = _mock_settings()
        obj = _make_instance(_prediction_with_diagram('```mermaid\ngraph LR\nA["`file`"] --> B\n```'))
        obj._prepare_data()
        assert obj.data['changes_diagram'] == '\n```mermaid\ngraph LR\nA["file"] --> B\n```'

    @patch('pr_insight.tools.pr_description.get_settings')
    def test_backticks_outside_label_are_kept(self, mock_get_settings):
        mock_get_settings.return_value = _mock_settings()
        obj = _make_instance(_prediction_with_diagram('```mermaid\ngraph LR\nA["`file`"] -->|`edge`| B\n```'))
        obj._prepare_data()
        assert obj.data['changes_diagram'] == '\n```mermaid\ngraph LR\nA["file"] -->|`edge`| B\n```'

    @patch('pr_insight.tools.pr_description.get_settings')
    def test_normal_diagram_only_adds_newline(self, mock_get_settings):
        mock_get_settings.return_value = _mock_settings()
        obj = _make_instance(_prediction_with_diagram('```mermaid\ngraph LR\nA["file.py"] --> B["output"]\n```'))
        obj._prepare_data()
        assert obj.data['changes_diagram'] == '\n```mermaid\ngraph LR\nA["file.py"] --> B["output"]\n```'

    def test_none_input_returns_empty(self):
        assert sanitize_diagram(None) == ''

    def test_non_string_input_returns_empty(self):
        assert sanitize_diagram(123) == ''

    def test_non_mermaid_fence_returns_empty(self):
        assert sanitize_diagram('```python\nprint("hello")\n```') == ''

class TestPRDescription:
    """Test suite for PR Description tool."""

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
        provider.get_pr_id.return_value = 123
        return provider

    def test_pr_description_initialization(self, mock_git_provider):
        """Test PRDescription initialization."""
        with patch("pr_insight.tools.pr_description.get_git_provider_with_context", return_value=mock_git_provider):
            with patch("pr_insight.tools.pr_description.LiteLLMAIHandler") as mock_handler:
                mock_handler_instance = MagicMock()
                mock_handler.return_value = mock_handler_instance
                desc = PRDescription(pr_url="https://github.com/owner/repo/pull/1")
                assert desc.git_provider is not None

    def test_pr_description_pr_id(self, mock_git_provider):
        """Test PRDescription has pr_id."""
        with patch("pr_insight.tools.pr_description.get_git_provider_with_context", return_value=mock_git_provider):
            with patch("pr_insight.tools.pr_description.LiteLLMAIHandler") as mock_handler:
                mock_handler_instance = MagicMock()
                mock_handler.return_value = mock_handler_instance
                desc = PRDescription(pr_url="https://github.com/owner/repo/pull/1")
                assert hasattr(desc, "pr_id")

    def test_pr_description_has_required_attributes(self, mock_git_provider):
        """Test PRDescription has required attributes."""
        with patch("pr_insight.tools.pr_description.get_git_provider_with_context", return_value=mock_git_provider):
            with patch("pr_insight.tools.pr_description.LiteLLMAIHandler") as mock_handler:
                mock_handler_instance = MagicMock()
                mock_handler.return_value = mock_handler_instance
                desc = PRDescription(pr_url="https://github.com/owner/repo/pull/1")
                assert hasattr(desc, "git_provider")
                assert hasattr(desc, "main_pr_language")
                assert hasattr(desc, "pr_id")
