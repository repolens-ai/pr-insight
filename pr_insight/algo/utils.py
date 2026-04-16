"""
Aggregator module for pr_insight utilities.

This module re-exports commonly used utilities from specialized submodules
to maintain backward compatibility and provide a unified import interface.
"""

from __future__ import annotations

import json
import os

from pr_insight.algo import MAX_TOKENS
from pr_insight.algo.common import (
    ModelType,
    PRDescriptionHeader,
    PRReviewHeader,
    Range,
    ReasoningEffort,
    TodoItem,
)
from pr_insight.algo.github_utils import (
    convert_str_to_datetime,
    get_rate_limit_status,
    validate_and_await_rate_limit,
    validate_rate_limit_github,
)
from pr_insight.algo.markdown_utils import (
    convert_to_markdown_v2,
    extract_relevant_lines_str,
    format_todo_item,
    format_todo_items,
    parse_code_suggestion,
    process_can_be_split,
    ticket_markdown_logic,
    unique_strings,
)
from pr_insight.algo.parser_utils import (
    fix_json_escape_char,
    load_yaml,
    try_fix_json,
    try_fix_yaml,
    update_settings_from_args,
)
from pr_insight.algo.patch_utils import (
    find_line_number_of_relevant_line_in_file,
    load_large_diff,
    set_file_languages,
)
from pr_insight.config_loader import get_settings
from pr_insight.log import get_logger
from pr_insight.algo.settings_utils import (
    get_model,
    get_setting,
    get_user_labels,
    is_value_no,
    process_description,
    replace_code_tags,
    set_custom_labels,
    set_pr_string,
    show_relevant_configurations,
    get_version,
    string_to_uniform_number,
)


def get_max_tokens(model):
    settings = get_settings()
    if model in MAX_TOKENS:
        max_tokens_model = MAX_TOKENS[model]
    elif settings.config.custom_model_max_tokens > 0:
        max_tokens_model = settings.config.custom_model_max_tokens
    else:
        get_logger().error(
            f"Model {model} is not defined in MAX_TOKENS in ./pr_insight/algo/__init__.py "
            "and no custom_model_max_tokens is set"
        )
        raise Exception(
            f"Ensure {model} is defined in MAX_TOKENS in ./pr_insight/algo/__init__.py "
            "or set a positive value for it in config.custom_model_max_tokens"
        )

    if settings.config.max_model_tokens and settings.config.max_model_tokens > 0:
        max_tokens_model = min(settings.config.max_model_tokens, max_tokens_model)
    return max_tokens_model


def clip_tokens(
    text: str,
    max_tokens: int,
    add_three_dots=True,
    num_input_tokens=None,
    delete_last_line=False,
) -> str:
    if not text:
        return text

    try:
        if num_input_tokens is None:
            from pr_insight.algo.token_handler import TokenEncoder

            encoder = TokenEncoder.get_token_encoder()
            num_input_tokens = len(encoder.encode(text))
        if num_input_tokens <= max_tokens:
            return text
        if max_tokens < 0:
            return ""

        num_chars = len(text)
        chars_per_token = num_chars / num_input_tokens
        factor = 0.9
        num_output_chars = int(factor * chars_per_token * max_tokens)

        if num_output_chars > 0:
            clipped_text = text[:num_output_chars]
            if delete_last_line:
                clipped_text = clipped_text.rsplit("\n", 1)[0]
            if add_three_dots:
                clipped_text += "\n...(truncated)"
        else:
            clipped_text = ""

        return clipped_text
    except Exception as e:
        get_logger().warning(f"Failed to clip tokens: {e}")
        return text


def github_action_output(output_data: dict, key_name: str):
    try:
        if not get_settings().get("github_action_config.enable_output", False):
            return

        key_data = output_data.get(key_name, {})
        with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
            print(f"{key_name}={json.dumps(key_data, indent=None, ensure_ascii=False)}", file=fh)
    except Exception as e:
        get_logger().error(f"Failed to write to GitHub Action output: {e}")

__all__ = [
    "MAX_TOKENS",
    "ModelType",
    "PRDescriptionHeader",
    "PRReviewHeader",
    "Range",
    "ReasoningEffort",
    "TodoItem",
    "convert_str_to_datetime",
    "get_rate_limit_status",
    "validate_and_await_rate_limit",
    "validate_rate_limit_github",
    "convert_to_markdown_v2",
    "extract_relevant_lines_str",
    "format_todo_item",
    "format_todo_items",
    "parse_code_suggestion",
    "process_can_be_split",
    "ticket_markdown_logic",
    "unique_strings",
    "fix_json_escape_char",
    "load_yaml",
    "try_fix_json",
    "try_fix_yaml",
    "update_settings_from_args",
    "find_line_number_of_relevant_line_in_file",
    "load_large_diff",
    "set_file_languages",
    "get_settings",
    "clip_tokens",
    "get_max_tokens",
    "get_model",
    "get_setting",
    "get_user_labels",
    "github_action_output",
    "is_value_no",
    "process_description",
    "replace_code_tags",
    "set_custom_labels",
    "set_pr_string",
    "show_relevant_configurations",
    "get_version",
    "string_to_uniform_number",
]
