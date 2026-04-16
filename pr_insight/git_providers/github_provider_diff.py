from __future__ import annotations

import copy
import difflib
import hashlib
import re
import traceback
from typing import List, Tuple

from starlette_context import context

from ..algo.file_filter import filter_ignored
from ..algo.git_patch_processing import extract_hunk_headers
from ..algo.language_handler import is_valid_file
from ..algo.types import EDIT_TYPE
from ..algo.common import PRReviewHeader
from ..algo.utils import (
    find_line_number_of_relevant_line_in_file,
    load_large_diff,
    set_file_languages,
)
from ..config_loader import get_settings
from ..log import get_logger
from .git_provider import MAX_FILES_ALLOWED_FULL, FilePatchInfo


class GithubProviderDiffMixin:
    def get_incremental_commits(self, incremental):
        self.incremental = incremental
        if self.incremental.is_incremental:
            self.unreviewed_files_set = dict()
            self._get_incremental_commits()

    def _get_incremental_commits(self):
        if not self.pr_commits:
            self.pr_commits = list(self.pr.get_commits())

        self.previous_review = self.get_previous_review(full=True, incremental=True)
        if self.previous_review:
            self.incremental.commits_range = self.get_commit_range()
            for commit in self.incremental.commits_range:
                if commit.commit.message.startswith(
                    f"Merge branch '{self._get_repo().default_branch}'"
                ):
                    get_logger().info(f"Skipping merge commit {commit.commit.message}")
                    continue
                self.unreviewed_files_set.update({file.filename: file for file in commit.files})
        else:
            get_logger().info("No previous review found, will review the entire PR")
            self.incremental.is_incremental = False

    def get_commit_range(self):
        last_review_time = self.previous_review.created_at
        first_new_commit_index = None
        for index in range(len(self.pr_commits) - 1, -1, -1):
            if self.pr_commits[index].commit.author.date > last_review_time:
                self.incremental.first_new_commit = self.pr_commits[index]
                first_new_commit_index = index
            else:
                self.incremental.last_seen_commit = self.pr_commits[index]
                break
        return self.pr_commits[first_new_commit_index:] if first_new_commit_index is not None else []

    def get_previous_review(self, *, full: bool, incremental: bool):
        if not (full or incremental):
            raise ValueError("At least one of full or incremental must be True")
        if not getattr(self, "comments", None):
            self.comments = list(self.pr.get_issue_comments())
        prefixes = []
        if full:
            prefixes.append(PRReviewHeader.REGULAR.value)
        if incremental:
            prefixes.append(PRReviewHeader.INCREMENTAL.value)
        for index in range(len(self.comments) - 1, -1, -1):
            if any(self.comments[index].body.startswith(prefix) for prefix in prefixes):
                return self.comments[index]

    def get_files(self):
        if self.incremental.is_incremental and self.unreviewed_files_set:
            return self.unreviewed_files_set.values()
        try:
            git_files = context.get("git_files", None)
            if git_files:
                return git_files
            self.git_files = list(self.pr.get_files())
            context["git_files"] = self.git_files
            return self.git_files
        except Exception:
            if not self.git_files:
                self.git_files = list(self.pr.get_files())
            return self.git_files

    def get_num_of_files(self):
        if hasattr(self.git_files, "totalCount"):
            return self.git_files.totalCount
        try:
            return len(self.git_files)
        except Exception:
            return -1

    def get_diff_files(self) -> list[FilePatchInfo]:
        try:
            try:
                diff_files = context.get("diff_files", None)
                if diff_files:
                    return diff_files
            except Exception:
                pass

            if self.diff_files:
                return self.diff_files

            files_original = self.get_files()
            files = filter_ignored(files_original)
            if files_original != files:
                try:
                    names_original = [file.filename for file in files_original]
                    names_new = [file.filename for file in files]
                    get_logger().info(
                        "Filtered out [ignore] files for pull request:",
                        extra={"files": names_original, "filtered_files": names_new},
                    )
                except Exception:
                    pass

            diff_files: list[FilePatchInfo] = []
            invalid_files_names = []
            is_close_to_rate_limit = False

            repo = self.repo_obj
            pr = self.pr
            try:
                compare = repo.compare(pr.base.sha, pr.head.sha)
                merge_base_commit = compare.merge_base_commit
            except Exception as e:
                get_logger().error(f"Failed to get merge base commit: {e}")
                merge_base_commit = pr.base
            if merge_base_commit.sha != pr.base.sha:
                get_logger().info(
                    f"Using merge base commit {merge_base_commit.sha} instead of base commit "
                )

            counter_valid = 0
            for file in files:
                if not is_valid_file(file.filename):
                    invalid_files_names.append(file.filename)
                    continue

                patch = file.patch
                if is_close_to_rate_limit:
                    new_file_content_str = ""
                    original_file_content_str = ""
                else:
                    counter_valid += 1
                    avoid_load = False
                    if counter_valid >= MAX_FILES_ALLOWED_FULL and patch and not self.incremental.is_incremental:
                        avoid_load = True
                        if counter_valid == MAX_FILES_ALLOWED_FULL:
                            get_logger().info(
                                "Too many files in PR, will avoid loading full content for rest of files"
                            )

                    if avoid_load:
                        new_file_content_str = ""
                    else:
                        new_file_content_str = self._get_pr_file_content(file, self.pr.head.sha)

                    if self.incremental.is_incremental and self.unreviewed_files_set:
                        original_file_content_str = self._get_pr_file_content(
                            file, self.incremental.last_seen_commit_sha
                        )
                        patch = load_large_diff(file.filename, new_file_content_str, original_file_content_str)
                        self.unreviewed_files_set[file.filename] = patch
                    else:
                        if avoid_load:
                            original_file_content_str = ""
                        else:
                            original_file_content_str = self._get_pr_file_content(file, merge_base_commit.sha)
                        if not patch:
                            patch = load_large_diff(file.filename, new_file_content_str, original_file_content_str)

                if file.status == "added":
                    edit_type = EDIT_TYPE.ADDED
                elif file.status == "removed":
                    edit_type = EDIT_TYPE.DELETED
                elif file.status == "renamed":
                    edit_type = EDIT_TYPE.RENAMED
                elif file.status == "modified":
                    edit_type = EDIT_TYPE.MODIFIED
                else:
                    get_logger().error(f"Unknown edit type: {file.status}")
                    edit_type = EDIT_TYPE.UNKNOWN

                if hasattr(file, "additions") and hasattr(file, "deletions"):
                    num_plus_lines = file.additions
                    num_minus_lines = file.deletions
                else:
                    patch_lines = patch.splitlines(keepends=True)
                    num_plus_lines = len([line for line in patch_lines if line.startswith('+')])
                    num_minus_lines = len([line for line in patch_lines if line.startswith('-')])

                file_patch_canonical_structure = FilePatchInfo(
                    original_file_content_str,
                    new_file_content_str,
                    patch,
                    file.filename,
                    edit_type=edit_type,
                    num_plus_lines=num_plus_lines,
                    num_minus_lines=num_minus_lines,
                )
                diff_files.append(file_patch_canonical_structure)
            if invalid_files_names:
                get_logger().info(f"Filtered out files with invalid extensions: {invalid_files_names}")

            self.diff_files = diff_files
            try:
                context["diff_files"] = diff_files
            except Exception:
                pass

            return diff_files

        except Exception as e:
            get_logger().error(
                f"Failing to get diff files: {e}",
                artifact={"traceback": traceback.format_exc()},
            )
            raise RateLimitExceeded("Rate limit exceeded for GitHub API.") from e

    def generate_link_to_relevant_line_number(self, suggestion) -> str:
        try:
            relevant_file = suggestion['relevant_file'].strip('`').strip("'").strip('\n')
            relevant_line_str = suggestion['relevant_line'].strip('\n')
            if not relevant_line_str:
                return ""

            position, absolute_position = find_line_number_of_relevant_line_in_file(
                self.diff_files, relevant_file, relevant_line_str
            )

            if absolute_position != -1:
                sha_file = hashlib.sha256(relevant_file.encode('utf-8')).hexdigest()
                link = (
                    f"{self.base_url_html}/{self.repo}/pull/{self.pr_num}/files#diff-{sha_file}R{absolute_position}"
                )
                return link
        except Exception as e:
            get_logger().info(f"Failed adding line link, error: {e}")

        return ""

    def get_line_link(self, relevant_file: str, relevant_line_start: int, relevant_line_end: int = None) -> str:
        sha_file = hashlib.sha256(relevant_file.encode('utf-8')).hexdigest()
        if relevant_line_start == -1:
            return f"{self.base_url_html}/{self.repo}/pull/{self.pr_num}/files#diff-{sha_file}"
        if relevant_line_end:
            return f"{self.base_url_html}/{self.repo}/pull/{self.pr_num}/files#diff-{sha_file}R{relevant_line_start}-R{relevant_line_end}"
        return f"{self.base_url_html}/{self.repo}/pull/{self.pr_num}/files#diff-{sha_file}R{relevant_line_start}"

    def validate_comments_inside_hunks(self, code_suggestions):
        code_suggestions_copy = copy.deepcopy(code_suggestions)
        diff_files = self.get_diff_files()
        RE_HUNK_HEADER = re.compile(
            r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[ ]?(.*)"
        )

        diff_files = set_file_languages(diff_files)

        for suggestion in code_suggestions_copy:
            try:
                relevant_file_path = suggestion['relevant_file']
                for file in diff_files:
                    if file.filename == relevant_file_path:
                        patch_str = file.patch
                        if not hasattr(file, 'patches_range'):
                            file.patches_range = []
                            patch_lines = patch_str.splitlines()
                            for i, line in enumerate(patch_lines):
                                if line.startswith('@@'):
                                    match = RE_HUNK_HEADER.match(line)
                                    if match:
                                        section_header, size1, size2, start1, start2 = extract_hunk_headers(match)
                                        file.patches_range.append({'start': start2, 'end': start2 + size2 - 1})

                        patches_range = file.patches_range
                        comment_start_line = suggestion.get('relevant_lines_start', None)
                        comment_end_line = suggestion.get('relevant_lines_end', None)
                        original_suggestion = suggestion.get('original_suggestion', None)
                        if not comment_start_line or not comment_end_line or not original_suggestion:
                            continue

                        is_valid_hunk = False
                        min_distance = float('inf')
                        patch_range_min = None
                        for patch_range in patches_range:
                            d1 = comment_start_line - patch_range['start']
                            d2 = patch_range['end'] - comment_end_line
                            if d1 >= 0 and d2 >= 0:
                                is_valid_hunk = True
                                min_distance = 0
                                patch_range_min = patch_range
                                break
                            elif d1 * d2 <= 0:
                                d1_clip = abs(min(0, d1))
                                d2_clip = abs(min(0, d2))
                                d = max(d1_clip, d2_clip)
                                if d < min_distance:
                                    patch_range_min = patch_range
                                    min_distance = min(min_distance, d)
                        if not is_valid_hunk:
                            if min_distance < 10:
                                suggestion['relevant_lines_start'] = max(
                                    suggestion['relevant_lines_start'], patch_range_min['start']
                                )
                                suggestion['relevant_lines_end'] = min(
                                    suggestion['relevant_lines_end'], patch_range_min['end']
                                )
                                body = suggestion['body'].strip()
                                existing_code = original_suggestion['existing_code'].rstrip() + "\n"
                                improved_code = original_suggestion['improved_code'].rstrip() + "\n"
                                diff = difflib.unified_diff(existing_code.split('\n'), improved_code.split('\n'), n=999)
                                patch_orig = "\n".join(diff)
                                patch = "\n".join(patch_orig.splitlines()[5:]).strip('\n')
                                diff_code = (
                                    "\n\n<details><summary>New proposed code:</summary>\n\n```diff\n"
                                    + patch.rstrip()
                                    + "\n```"
                                )
                                body = re.sub(r'```suggestion.*?```', diff_code, body, flags=re.DOTALL)
                                body += "\n\n</details>"
                                suggestion['body'] = body
                                get_logger().info(
                                    f"Comment was moved to a valid hunk, "
                                    f"start_line={suggestion['relevant_lines_start']}, end_line={suggestion['relevant_lines_end']}, file={file.filename}"
                                )
                            else:
                                get_logger().error(
                                    f"Comment is not inside a valid hunk, "
                                    f"start_line={suggestion['relevant_lines_start']}, end_line={suggestion['relevant_lines_end']}, file={file.filename}"
                                )
            except Exception as e:
                get_logger().error(f"Failed to process patch for committable comment, error: {e}")
        return code_suggestions_copy
