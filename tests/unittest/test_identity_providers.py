import pytest
from pr_insight.identity_providers.identity_provider import IdentityProvider, Eligibility
from pr_insight.identity_providers.default_identity_provider import DefaultIdentityProvider
from unittest.mock import MagicMock


class TestIdentityProvider:
    def test_identity_provider_is_abstract(self):
        with pytest.raises(TypeError):
            IdentityProvider()


class TestDefaultIdentityProvider:
    def test_default_identity_provider_creation(self):
        provider = DefaultIdentityProvider()
        assert provider is not None

    def test_verify_eligibility(self):
        provider = DefaultIdentityProvider()
        mock_git_provider = MagicMock()
        result = provider.verify_eligibility(mock_git_provider, "user123", "https://github.com/owner/repo/pull/1")
        assert result == Eligibility.ELIGIBLE

    def test_inc_invocation_count(self):
        provider = DefaultIdentityProvider()
        mock_git_provider = MagicMock()
        provider.inc_invocation_count(mock_git_provider, "user123")
