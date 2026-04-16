from __future__ import annotations

from typing import Optional

from github import AppAuthentication, Auth, Github

from ..config_loader import get_settings
from ..log import get_logger


class GithubProviderAuthMixin:
    """Handles GitHub authentication and client initialization."""

    def _get_github_client(self):
        self.deployment_type = get_settings().get("GITHUB.DEPLOYMENT_TYPE", "user")
        self.auth = None
        if self.deployment_type == "app":
            try:
                private_key = get_settings().github.private_key
                app_id = get_settings().github.app_id
            except AttributeError as e:
                raise ValueError(
                    "GitHub app ID and private key are required when using GitHub app deployment"
                ) from e
            if not self.installation_id:
                raise ValueError(
                    "GitHub app installation ID is required when using GitHub app deployment"
                )
            auth = AppAuthentication(
                app_id=app_id,
                private_key=private_key,
                installation_id=self.installation_id,
            )
            self.auth = auth
        elif self.deployment_type == "user":
            try:
                token = get_settings().github.user_token
            except AttributeError as e:
                raise ValueError(
                    "GitHub token is required when using user deployment. See: "
                    "https://github.com/khulnasoft/pr-insight#method-2-run-from-source"
                ) from e
            self.auth = Auth.Token(token)
        if self.auth:
            return Github(auth=self.auth, base_url=self.base_url)
        else:
            raise ValueError("Could not authenticate to GitHub")

    def _get_repo(self):
        if (
            hasattr(self, "repo_obj")
            and hasattr(self.repo_obj, "full_name")
            and self.repo_obj.full_name == self.repo
        ):
            return self.repo_obj
        else:
            self.repo_obj = self.github_client.get_repo(self.repo)
            return self.repo_obj

    def _get_pr(self):
        return self._get_repo().get_pull(self.pr_num)

    def _prepare_clone_url_with_token(self, repo_url_to_clone: str) -> str | None:
        try:
            if self.auth and self.deployment_type == "user":
                token = get_settings().github.user_token
                parsed_url = repo_url_to_clone.replace("https://", "").replace("http://", "")
                return f"https://x-access-token:{token}@{parsed_url}"
        except Exception:
            pass
        return None
