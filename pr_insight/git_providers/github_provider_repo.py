from __future__ import annotations

import hashlib
import itertools
import json
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urlparse

from ..algo.utils import Range
from ..algo.utils import clip_tokens
from ..config_loader import get_settings
from ..log import get_logger
from .git_provider import FilePatchInfo


class GithubProviderRepoMixin:
    def _get_owner_and_repo_path(self, given_url: str) -> str:
        try:
            repo_path = None
            if 'issues' in given_url:
                repo_path, _ = self._parse_issue_url(given_url)
            elif 'pull' in given_url:
                repo_path, _ = self._parse_pr_url(given_url)
            elif given_url.endswith('.git'):
                parsed_url = urlparse(given_url)
                repo_path = (parsed_url.path.split('.git')[0])[1:]
            if not repo_path:
                get_logger().error(
                    f"url is neither an issues url nor a PR url nor a valid git url: {given_url}. Returning empty result."
                )
                return ""
            return repo_path
        except Exception:
            get_logger().exception(f"unable to parse url: {given_url}. Returning empty result.")
            return ""

    def get_git_repo_url(self, issues_or_pr_url: str) -> str:
        repo_path = self._get_owner_and_repo_path(issues_or_pr_url)
        if not repo_path or repo_path not in issues_or_pr_url:
            get_logger().error(f"Unable to retrieve owner/path from url: {issues_or_pr_url}")
            return ""
        return f"{self.base_url_html}/{repo_path}.git"

    def get_canonical_url_parts(self, repo_git_url: str, desired_branch: str) -> Tuple[str, str]:
        owner = None
        repo = None
        scheme_and_netloc = None

        if repo_git_url or self.issue_main:
            desired_branch = desired_branch if repo_git_url else self.issue_main.repository.default_branch
            html_url = repo_git_url if repo_git_url else self.issue_main.html_url
            parsed_git_url = urlparse(html_url)
            scheme_and_netloc = parsed_git_url.scheme + "://" + parsed_git_url.netloc
            repo_path = self._get_owner_and_repo_path(html_url)
            if repo_path.count('/') == 1:
                owner, repo = repo_path.split('/')
            else:
                get_logger().error(f"Invalid repo_path: {repo_path} from url: {html_url}")
                return "", ""

        if (not owner or not repo) and self.repo:
            owner, repo = self.repo.split('/')
            scheme_and_netloc = self.base_url_html
            desired_branch = self.repo_obj.default_branch
        if not all([scheme_and_netloc, owner, repo]):
            get_logger().error(
                "Unable to get canonical url parts since missing context (PR or explicit git url)"
            )
            return "", ""

        prefix = f"{scheme_and_netloc}/{owner}/{repo}/blob/{desired_branch}"
        suffix = ""
        return prefix, suffix

    def get_pr_url(self) -> str:
        return self.pr.html_url

    def set_pr(self, pr_url: str):
        self.repo, self.pr_num = self._parse_pr_url(pr_url)
        self.pr = self._get_pr()

    def _parse_pr_url(self, pr_url: str) -> Tuple[str, int]:
        parsed_url = urlparse(pr_url)
        if parsed_url.path.startswith('/api/v3'):
            parsed_url = urlparse(pr_url.replace("/api/v3", ""))

        path_parts = parsed_url.path.strip('/').split('/')
        if 'api.github.com' in parsed_url.netloc or '/api/v3' in pr_url:
            if len(path_parts) < 5 or path_parts[3] != 'pulls':
                raise ValueError("The provided URL does not appear to be a GitHub PR URL")
            repo_name = '/'.join(path_parts[1:3])
            try:
                pr_number = int(path_parts[4])
            except ValueError as e:
                raise ValueError("Unable to convert PR number to integer") from e
            return repo_name, pr_number

        if len(path_parts) < 4 or path_parts[2] != 'pull':
            raise ValueError("The provided URL does not appear to be a GitHub PR URL")

        repo_name = '/'.join(path_parts[:2])
        try:
            pr_number = int(path_parts[3])
        except ValueError as e:
            raise ValueError("Unable to convert PR number to integer") from e

        return repo_name, pr_number

    def _parse_issue_url(self, issue_url: str) -> Tuple[str, int]:
        parsed_url = urlparse(issue_url)
        if parsed_url.path.startswith('/api/v3'):
            parsed_url = urlparse(issue_url.replace("/api/v3", ""))

        path_parts = parsed_url.path.strip('/').split('/')
        if 'api.github.com' in parsed_url.netloc or '/api/v3' in issue_url:
            if len(path_parts) < 5 or path_parts[3] != 'issues':
                raise ValueError("The provided URL does not appear to be a GitHub ISSUE URL")
            repo_name = '/'.join(path_parts[1:3])
            try:
                issue_number = int(path_parts[4])
            except ValueError as e:
                raise ValueError("Unable to convert issue number to integer") from e
            return repo_name, issue_number

        if len(path_parts) < 4 or path_parts[2] != 'issues':
            raise ValueError("The provided URL does not appear to be a GitHub PR issue")

        repo_name = '/'.join(path_parts[:2])
        try:
            issue_number = int(path_parts[3])
        except ValueError as e:
            raise ValueError("Unable to convert issue number to integer") from e

        return repo_name, issue_number

    def get_pr_file_content(self, file_path: str, branch: str) -> str:
        try:
            file_content_str = str(
                self._get_repo()
                .get_contents(file_path, ref=branch)
                .decoded_content.decode()
            )
        except Exception:
            file_content_str = ""
        return file_content_str

    def create_or_update_pr_file(
        self, file_path: str, branch: str, contents="", message=""
    ) -> None:
        try:
            file_obj = self._get_repo().get_contents(file_path, ref=branch)
            sha1 = file_obj.sha
        except Exception:
            sha1 = ""
        self.repo_obj.update_file(
            path=file_path,
            message=message,
            content=contents,
            sha=sha1,
            branch=branch,
        )

    def _get_pr_file_content(self, file: FilePatchInfo, sha: str) -> str:
        return self.get_pr_file_content(file.filename, sha)

    def publish_labels(self, pr_types):
        try:
            label_color_map = {
                "Bug fix": "1d76db",
                "Tests": "e99695",
                "Bug fix with tests": "c5def5",
                "Enhancement": "bfd4f2",
                "Documentation": "d4c5f9",
                "Other": "d1bcf9",
            }
            post_parameters = []
            for p in pr_types:
                color = label_color_map.get(p, "d1bcf9")
                post_parameters.append({"name": p, "color": color})
            self.pr._requester.requestJsonAndCheck(
                "PUT", f"{self.pr.issue_url}/labels", input=post_parameters
            )
        except Exception as e:
            get_logger().warning(f"Failed to publish labels, error: {e}")

    def get_pr_labels(self, update=False):
        try:
            if not update:
                return [label.name for label in self.pr.labels]
            headers, labels = self.pr._requester.requestJsonAndCheck(
                "GET", f"{self.pr.issue_url}/labels"
            )
            return [label['name'] for label in labels]
        except Exception as e:
            get_logger().exception(f"Failed to get labels, error: {e}")
            return []

    def get_repo_labels(self):
        labels = self.repo_obj.get_labels()
        return [label for label in itertools.islice(labels, 50)]

    def get_commit_messages(self):
        max_tokens = get_settings().get("CONFIG.MAX_COMMITS_TOKENS", None)
        try:
            commit_list = self.pr.get_commits()
            commit_messages = [commit.commit.message for commit in commit_list]
            commit_messages_str = "\n".join(
                [f"{i + 1}. {message}" for i, message in enumerate(commit_messages)]
            )
        except Exception:
            commit_messages_str = ""
        if max_tokens:
            commit_messages_str = clip_tokens(commit_messages_str, max_tokens)
        return commit_messages_str

    def publish_description(self, pr_title: str, pr_body: str):
        self.pr.edit(title=pr_title, body=pr_body)

    def get_latest_commit_url(self) -> str:
        return self.last_commit_id.html_url

    def get_title(self):
        return self.pr.title

    def get_languages(self):
        languages = self._get_repo().get_languages()
        return languages

    def get_pr_branch(self):
        return self.pr.head.ref

    def get_pr_owner_id(self) -> str | None:
        if not self.repo:
            return None
        return self.repo.split('/') [0]

    def get_pr_description_full(self):
        return self.pr.body

    def get_user_id(self):
        if not self.github_user_id:
            try:
                self.github_user_id = self.github_client.get_user().raw_data['login']
            except Exception:
                self.github_user_id = ""
        return self.github_user_id

    def get_notifications(self, since: datetime):
        deployment_type = get_settings().get("GITHUB.DEPLOYMENT_TYPE", "user")
        if deployment_type != 'user':
            raise ValueError("Deployment mode must be set to 'user' to get notifications")
        return self.github_client.get_user().get_notifications(since=since)

    def get_issue_comments(self):
        return self.pr.get_issue_comments()

    def get_repo_settings(self):
        try:
            contents = self.repo_obj.get_contents(".pr_insight.toml").decoded_content
            return contents
        except Exception:
            return ""

    def get_workspace_name(self):
        return self.repo.split('/')[0]

    def add_eyes_reaction(self, issue_comment_id: int, disable_eyes: bool = False) -> Optional[int]:
        if disable_eyes:
            return None
        try:
            headers, data_patch = self.pr._requester.requestJsonAndCheck(
                "POST",
                f"{self.base_url}/repos/{self.repo}/issues/comments/{issue_comment_id}/reactions",
                input={"content": "eyes"},
            )
            return data_patch.get("id", None)
        except Exception as e:
            get_logger().warning(f"Failed to add eyes reaction, error: {e}")
            return None

    def remove_reaction(self, issue_comment_id: int, reaction_id: str) -> bool:
        try:
            self.pr._requester.requestJsonAndCheck(
                "DELETE",
                f"{self.base_url}/repos/{self.repo}/issues/comments/{issue_comment_id}/reactions/{reaction_id}",
            )
            return True
        except Exception as e:
            get_logger().exception(f"Failed to remove eyes reaction, error: {e}")
            return False

    def fetch_sub_issues(self, issue_url):
        sub_issues = set()
        parts = issue_url.rstrip("/").split("/")
        owner, repo, issue_number = parts[-4], parts[-3], parts[-1]

        try:
            query = f"""
            query {{
                repository(owner: \"{owner}\", name: \"{repo}\") {{
                    issue(number: {issue_number}) {{
                        id
                    }}
                }}
            }}
            """
            response_tuple = self.github_client._Github__requester.requestJson(
                "POST", "/graphql", input={"query": query}
            )
            if isinstance(response_tuple, tuple) and len(response_tuple) == 3:
                response_json = json.loads(response_tuple[2])
            else:
                get_logger().error(f"Unexpected response format: {response_tuple}")
                return sub_issues

            issue_id = response_json.get("data", {}).get("repository", {}).get("issue", {}).get("id")
            if not issue_id:
                get_logger().warning(f"Issue ID not found for {issue_url}")
                return sub_issues

            sub_issues_query = f"""
            query {{
                node(id: \"{issue_id}\") {{
                    ... on Issue {{
                        subIssues(first: 10) {{
                            nodes {{
                                url
                            }}
                        }}
                    }}
                }}
            }}
            """
            sub_issues_response_tuple = self.github_client._Github__requester.requestJson(
                "POST", "/graphql", input={"query": sub_issues_query}
            )
            if isinstance(sub_issues_response_tuple, tuple) and len(sub_issues_response_tuple) == 3:
                sub_issues_response_json = json.loads(sub_issues_response_tuple[2])
            else:
                get_logger().error(
                    "Unexpected sub-issues response format",
                    artifact={"response": sub_issues_response_tuple},
                )
                return sub_issues

            if not sub_issues_response_json.get("data", {}).get("node", {}).get("subIssues"):
                get_logger().error("Invalid sub-issues response structure")
                return sub_issues

            nodes = sub_issues_response_json.get("data", {}).get("node", {}).get("subIssues", {}).get("nodes", [])
            get_logger().info(
                f"Github Sub-issues fetched: {len(nodes)}",
                artifact={"nodes": nodes},
            )

            for sub_issue in nodes:
                if "url" in sub_issue:
                    sub_issues.add(sub_issue["url"])
        except Exception as e:
            get_logger().exception(f"Failed to fetch sub-issues. Error: {e}")
        return sub_issues

    def auto_approve(self) -> bool:
        try:
            res = self.pr.create_review(event="APPROVE")
            if res.state == "APPROVED":
                return True
            return False
        except Exception as e:
            get_logger().exception(f"Failed to auto-approve, error: {e}")
            return False

    def calc_pr_statistics(self, pull_request_data: dict):
        return {}

    def get_lines_link_original_file(self, filepath: str, component_range: Range) -> str:
        line_start = component_range.line_start + 1
        line_end = component_range.line_end + 1
        return (
            f"{self.base_url_html}/{self.repo}/blob/{self.last_commit_id.sha}/{filepath}/"
            f"#L{line_start}-L{line_end}"
        )

    def get_pr_id(self):
        try:
            return f"{self.repo}/{self.pr_num}"
        except Exception:
            return ""
