from __future__ import annotations

import copy
import re
import time

from ..algo.utils import find_line_number_of_relevant_line_in_file
from ..config_loader import get_settings
from ..log import get_logger


class GithubProviderCommentsMixin:
    def publish_comment(self, pr_comment: str, is_temporary: bool = False):
        if not self.pr and not self.issue_main:
            get_logger().error("Cannot publish a comment if missing PR/Issue context")
            return None

        if is_temporary and not get_settings().config.publish_output_progress:
            get_logger().debug(f"Skipping publish_comment for temporary comment: {pr_comment}")
            return None
        pr_comment = self.limit_output_characters(pr_comment, self.max_comment_chars)

        if self.issue_main:
            return self.issue_main.create_comment(pr_comment)

        response = self.pr.create_issue_comment(pr_comment)
        if hasattr(response, "user") and hasattr(response.user, "login"):
            self.github_user_id = response.user.login
        response.is_temporary = is_temporary
        if not hasattr(self.pr, 'comments_list'):
            self.pr.comments_list = []
        self.pr.comments_list.append(response)
        return response

    def get_comment_url(self, comment) -> str:
        return comment.html_url

    def publish_persistent_comment(
        self,
        pr_comment: str,
        initial_header: str,
        update_header: bool = True,
        name="review",
        final_update_message=True,
    ):
        self.publish_persistent_comment_full(
            pr_comment,
            initial_header,
            update_header,
            name,
            final_update_message,
        )

    def publish_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str, original_suggestion=None):
        body = self.limit_output_characters(body, self.max_comment_chars)
        self.publish_inline_comments([self.create_inline_comment(body, relevant_file, relevant_line_in_file)])

    def create_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str,
                              absolute_position: int = None):
        body = self.limit_output_characters(body, self.max_comment_chars)
        position, absolute_position = find_line_number_of_relevant_line_in_file(
            self.diff_files,
            relevant_file.strip('`'),
            relevant_line_in_file,
            absolute_position,
        )
        if position == -1:
            get_logger().info(f"Could not find position for {relevant_file} {relevant_line_in_file}")
            subject_type = "FILE"
        else:
            subject_type = "LINE"
        path = relevant_file.strip()
        return dict(body=body, path=path, position=position) if subject_type == "LINE" else {}

    def publish_inline_comments(self, comments: list[dict], disable_fallback: bool = False):
        try:
            self.pr.create_review(commit=self.last_commit_id, comments=comments)
        except Exception as e:
            get_logger().info("Initially failed to publish inline comments as committable")

            if getattr(e, "status", None) == 422 and not disable_fallback:
                pass
            else:
                raise e

            try:
                self._publish_inline_comments_fallback_with_verification(comments)
            except Exception as err:
                get_logger().error(f"Failed to publish inline code comments fallback, error: {err}")
                raise err

    def get_review_thread_comments(self, comment_id: int) -> list[dict]:
        try:
            all_comments = list(self.pr.get_comments())
            target_comment = next((c for c in all_comments if c.id == comment_id), None)
            if not target_comment:
                return []

            root_comment_id = target_comment.raw_data.get("in_reply_to_id", target_comment.id)
            thread_comments = [
                c for c in all_comments if
                c.id == root_comment_id or c.raw_data.get("in_reply_to_id") == root_comment_id
            ]
            return thread_comments
        except Exception as e:
            get_logger().exception(
                "Failed to get review comments for an inline ask command",
                artifact={"comment_id": comment_id, "error": e},
            )
            return []

    def _publish_inline_comments_fallback_with_verification(self, comments: list[dict]):
        verified_comments, invalid_comments = self._verify_code_comments(comments)

        if verified_comments:
            try:
                self.pr.create_review(commit=self.last_commit_id, comments=verified_comments)
            except Exception:
                pass

        if invalid_comments and get_settings().github.try_fix_invalid_inline_comments:
            fixed_comments_as_one_liner = self._try_fix_invalid_inline_comments([
                comment for comment, _ in invalid_comments
            ])
            for comment in fixed_comments_as_one_liner:
                try:
                    self.publish_inline_comments([comment], disable_fallback=True)
                    get_logger().info(f"Published invalid comment as a single line comment: {comment}")
                except Exception:
                    get_logger().error(f"Failed to publish invalid comment as a single line comment: {comment}")

    def _verify_code_comment(self, comment: dict):
        is_verified = False
        e = None
        try:
            input_data = dict(commit_id=self.last_commit_id.sha, comments=[comment])
            headers, data = self.pr._requester.requestJsonAndCheck(
                "POST", f"{self.pr.url}/reviews", input=input_data,
            )
            pending_review_id = data["id"]
            is_verified = True
        except Exception as err:
            is_verified = False
            pending_review_id = None
            e = err
        if pending_review_id is not None:
            try:
                self.pr._requester.requestJsonAndCheck("DELETE", f"{self.pr.url}/reviews/{pending_review_id}")
            except Exception:
                pass
        return is_verified, e

    def _verify_code_comments(self, comments: list[dict]) -> tuple[list[dict], list[tuple[dict, Exception]]]:
        verified_comments = []
        invalid_comments = []
        for comment in comments:
            time.sleep(1)
            is_verified, e = self._verify_code_comment(comment)
            if is_verified:
                verified_comments.append(comment)
            else:
                invalid_comments.append((comment, e))
        return verified_comments, invalid_comments

    def _try_fix_invalid_inline_comments(self, invalid_comments: list[dict]) -> list[dict]:
        fixed_comments = []
        for comment in invalid_comments:
            try:
                fixed_comment = copy.deepcopy(comment)
                if "```suggestion" in comment["body"]:
                    fixed_comment["body"] = comment["body"].split("```suggestion")[0]
                if "start_line" in comment:
                    fixed_comment["line"] = comment["start_line"]
                    del fixed_comment["start_line"]
                if "start_side" in comment:
                    fixed_comment["side"] = comment["start_side"]
                    del fixed_comment["start_side"]
                if fixed_comment != comment:
                    fixed_comments.append(fixed_comment)
            except Exception as e:
                get_logger().error(f"Failed to fix inline comment, error: {e}")
        return fixed_comments

    def publish_code_suggestions(self, code_suggestions: list) -> bool:
        post_parameters_list = []

        code_suggestions_validated = self.validate_comments_inside_hunks(code_suggestions)

        for suggestion in code_suggestions_validated:
            body = suggestion['body']
            relevant_file = suggestion['relevant_file']
            relevant_lines_start = suggestion['relevant_lines_start']
            relevant_lines_end = suggestion['relevant_lines_end']

            if not relevant_lines_start or relevant_lines_start == -1:
                get_logger().exception(
                    f"Failed to publish code suggestion, relevant_lines_start is {relevant_lines_start}"
                )
                continue

            if relevant_lines_end < relevant_lines_start:
                get_logger().exception(
                    f"Failed to publish code suggestion, "
                    f"relevant_lines_end is {relevant_lines_end} and "
                    f"relevant_lines_start is {relevant_lines_start}"
                )
                continue

            if relevant_lines_end > relevant_lines_start:
                post_parameters = {
                    "body": body,
                    "path": relevant_file,
                    "line": relevant_lines_end,
                    "start_line": relevant_lines_start,
                    "start_side": "RIGHT",
                }
            else:
                post_parameters = {
                    "body": body,
                    "path": relevant_file,
                    "line": relevant_lines_start,
                    "side": "RIGHT",
                }
            post_parameters_list.append(post_parameters)

        try:
            self.publish_inline_comments(post_parameters_list)
            return True
        except Exception as e:
            get_logger().error(f"Failed to publish code suggestion, error: {e}")
            return False

    def edit_comment(self, comment, body: str):
        try:
            body = self.limit_output_characters(body, self.max_comment_chars)
            comment.edit(body=body)
        except Exception as e:
            if getattr(e, "status", None) == 403:
                get_logger().warning(
                    "Failed to edit github comment due to permission restrictions",
                    artifact={"error": e},
                )
            else:
                get_logger().exception(f"Failed to edit github comment", artifact={"error": e})

    def edit_comment_from_comment_id(self, comment_id: int, body: str):
        try:
            body = self.limit_output_characters(body, self.max_comment_chars)
            headers, data_patch = self.pr._requester.requestJsonAndCheck(
                "PATCH",
                f"{self.base_url}/repos/{self.repo}/issues/comments/{comment_id}",
                input={"body": body},
            )
        except Exception as e:
            get_logger().exception(f"Failed to edit comment, error: {e}")

    def reply_to_comment_from_comment_id(self, comment_id: int, body: str):
        try:
            body = self.limit_output_characters(body, self.max_comment_chars)
            headers, data_patch = self.pr._requester.requestJsonAndCheck(
                "POST",
                f"{self.base_url}/repos/{self.repo}/pulls/{self.pr_num}/comments/{comment_id}/replies",
                input={"body": body},
            )
        except Exception as e:
            get_logger().exception(f"Failed to reply comment, error: {e}")

    def get_comment_body_from_comment_id(self, comment_id: int):
        try:
            headers, data_patch = self.pr._requester.requestJsonAndCheck(
                "GET", f"{self.base_url}/repos/{self.repo}/issues/comments/{comment_id}"
            )
            return data_patch.get("body", "")
        except Exception as e:
            get_logger().exception(f"Failed to edit comment, error: {e}")
            return None

    def publish_file_comments(self, file_comments: list) -> bool:
        try:
            headers, existing_comments = self.pr._requester.requestJsonAndCheck(
                "GET", f"{self.pr.url}/comments"
            )
            for comment in file_comments:
                comment["commit_id"] = self.last_commit_id.sha
                comment["body"] = self.limit_output_characters(comment["body"], self.max_comment_chars)

                found = False
                for existing_comment in existing_comments:
                    comment["commit_id"] = self.last_commit_id.sha
                    our_app_name = get_settings().get("GITHUB.APP_NAME", "")
                    if self.deployment_type == 'app':
                        same_comment_creator = our_app_name.lower() in existing_comment["user"]["login"].lower()
                    else:
                        same_comment_creator = self.github_user_id == existing_comment["user"]["login"]
                    if existing_comment["subject_type"] == 'file' and comment["path"] == existing_comment["path"] and same_comment_creator:
                        headers, data_patch = self.pr._requester.requestJsonAndCheck(
                            "PATCH",
                            f"{self.base_url}/repos/{self.repo}/pulls/comments/{existing_comment['id']}",
                            input={"body": comment["body"]},
                        )
                        found = True
                        break
                if not found:
                    headers, data_post = self.pr._requester.requestJsonAndCheck(
                        "POST", f"{self.pr.url}/comments", input=comment
                    )
            return True
        except Exception as e:
            get_logger().error(f"Failed to publish diffview file summary, error: {e}")
            return False

    def remove_initial_comment(self):
        try:
            for comment in getattr(self.pr, 'comments_list', []):
                if comment.is_temporary:
                    self.remove_comment(comment)
        except Exception as e:
            get_logger().exception(f"Failed to remove initial comment, error: {e}")

    def remove_comment(self, comment):
        try:
            comment.delete()
        except Exception as e:
            get_logger().exception(f"Failed to remove comment, error: {e}")
