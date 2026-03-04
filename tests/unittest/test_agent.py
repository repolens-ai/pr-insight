from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from pr_insight.agent.pr_insight import PRAgent, command2class, commands


class TestPRAgent:
    """Test suite for PR Agent."""

    def test_command2class_contains_all_commands(self):
        """Verify all expected commands are in command2class."""
        expected_commands = [
            "auto_review", "answer", "review", "review_pr",
            "describe", "describe_pr", "improve", "improve_code",
            "ask", "ask_question", "ask_line",
            "update_changelog", "config", "settings",
            "help", "similar_issue", "add_docs",
            "generate_labels", "help_docs"
        ]
        for cmd in expected_commands:
            assert cmd in command2class, f"Command {cmd} not in command2class"

    def test_commands_list_contains_all_commands(self):
        """Verify commands list contains expected commands."""
        assert "review" in commands
        assert "describe" in commands
        assert "improve" in commands
        assert "ask" in commands

    def test_pr_agent_initialization(self):
        """Test PRAgent initialization."""
        agent = PRAgent()
        assert agent.ai_handler is not None

    def test_pr_agent_has_handle_request(self):
        """Test that PRAgent has _handle_request method."""
        agent = PRAgent()
        assert hasattr(agent, '_handle_request')
        assert callable(agent._handle_request)
