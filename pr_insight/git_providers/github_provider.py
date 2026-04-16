from typing import Optional

from github.Issue import Issue
from starlette_context import context

from ..config_loader import get_settings
from ..log import get_logger
from .git_provider import GitProvider, IncrementalPR
from .github_provider_auth import GithubProviderAuthMixin
from .github_provider_comments import GithubProviderCommentsMixin
from .github_provider_diff import GithubProviderDiffMixin
from .github_provider_repo import GithubProviderRepoMixin


class GithubProvider(
    GithubProviderAuthMixin,
    GithubProviderCommentsMixin,
    GithubProviderDiffMixin,
    GithubProviderRepoMixin,
    GitProvider,
):
    def __init__(self, pr_url: Optional[str] = None):
        self.repo_obj = None
        try:
            self.installation_id = context.get("installation_id", None)
        except Exception:
            self.installation_id = None
        self.max_comment_chars = 65000
        self.base_url = get_settings().get("GITHUB.BASE_URL", "https://api.github.com").rstrip("/")
        self.base_url_html = (
            self.base_url.split("api/")[0].rstrip("/")
            if "api/" in self.base_url
            else "https://github.com"
        )
        self.github_client = self._get_github_client()
        self.repo = None
        self.pr_num = None
        self.pr = None
        self.issue_main = None
        self.github_user_id = None
        self.diff_files = None
        self.git_files = None
        self.incremental = IncrementalPR(False)
        if pr_url and "pull" in pr_url:
            self.set_pr(pr_url)
            self.pr_commits = list(self.pr.get_commits())
            self.last_commit_id = self.pr_commits[-1]
            # GitHub Actions can provide an API URL, so normalize from the PR object.
            self.pr_url = self.get_pr_url()
        elif pr_url and "issue" in pr_url:
            self.issue_main = self._get_issue_handle(pr_url)
        else:
            self.pr_commits = None

    def _get_issue_handle(self, issue_url) -> Optional[Issue]:
        repo_name, issue_number = self._parse_issue_url(issue_url)
        if not repo_name or not issue_number:
            get_logger().error(f"Given url: {issue_url} is not a valid issue.")
            return None
        try:
            repo_obj = self.github_client.get_repo(repo_name)
            if not repo_obj:
                get_logger().error(
                    f"Given url: {issue_url}, belonging to owner/repo: {repo_name} does "
                    f"not have a valid repository: {self.get_git_repo_url(issue_url)}"
                )
                return None
            return repo_obj.get_issue(issue_number)
        except Exception:
            get_logger().exception(
                f"Failed to get an issue object for issue: {issue_url}, belonging to owner/repo: {repo_name}"
            )
            return None

    def is_supported(self, capability: str) -> bool:
        return True
