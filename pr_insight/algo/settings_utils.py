from __future__ import annotations

import hashlib
import html
import json
import os
import re
import sys
import time
import traceback
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from typing import Any, List

import html2text
from starlette_context import context

from pr_insight.algo import MAX_TOKENS
from pr_insight.algo.common import PRDescriptionHeader, PRReviewHeader
from pr_insight.config_loader import get_settings, global_settings
from pr_insight.log import get_logger


def get_model(model_type: str = "model_weak") -> str:
    if model_type == "model_weak" and get_settings().get("config.model_weak"):
        return get_settings().config.model_weak
    elif model_type == "model_reasoning" and get_settings().get("config.model_reasoning"):
        return get_settings().config.model_reasoning
    return get_settings().config.model


def get_setting(key: str) -> Any:
    try:
        key = key.upper()
        return context.get("settings", global_settings).get(key, global_settings.get(key, None))
    except Exception:
        return global_settings.get(key, None)


def get_max_tokens(model):
    settings = get_settings()
    if model in MAX_TOKENS:
        max_tokens_model = MAX_TOKENS[model]
    elif settings.config.custom_model_max_tokens > 0:
        max_tokens_model = settings.config.custom_model_max_tokens
    else:
        get_logger().error(f"Model {model} is not defined in MAX_TOKENS in ./pr_insight/algo/__init__.py and no custom_model_max_tokens is set")
        raise Exception(f"Ensure {model} is defined in MAX_TOKENS in ./pr_insight/algo/__init__.py or set a positive value for it in config.custom_model_max_tokens")

    if settings.config.max_model_tokens and settings.config.max_model_tokens > 0:
        max_tokens_model = min(settings.config.max_model_tokens, max_tokens_model)
    return max_tokens_model


def clip_tokens(text: str, max_tokens: int, add_three_dots=True, num_input_tokens=None, delete_last_line=False) -> str:
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
                clipped_text = clipped_text.rsplit('\n', 1)[0]
            if add_three_dots:
                clipped_text += "\n...(truncated)"
        else:
            clipped_text = ""

        return clipped_text
    except Exception as e:
        get_logger().warning(f"Failed to clip tokens: {e}")
        return text


def replace_code_tags(text):
    text = html.escape(text)
    parts = text.split('`')
    for i in range(1, len(parts), 2):
        parts[i] = '<code>' + parts[i] + '</code>'
    return ''.join(parts)


def set_custom_labels(variables, git_provider=None):
    if not get_settings().config.enable_custom_labels:
        return

    labels = get_settings().get('custom_labels', {})
    if not labels:
        labels = ['Bug fix', 'Tests', 'Bug fix with tests', 'Enhancement', 'Documentation', 'Other']
        labels_list = "\n      - ".join(labels) if labels else ""
        labels_list = f"      - {labels_list}" if labels_list else ""
        variables["custom_labels"] = labels_list
        return

    variables["custom_labels_class"] = "class Label(str, Enum):"
    labels_minimal_to_labels_dict = {}
    for k, v in labels.items():
        description = "'" + v['description'].strip('\n').replace('\n', '\\n') + "'"
        variables["custom_labels_class"] += f"\n    {k.lower().replace(' ', '_')} = {description}"
        labels_minimal_to_labels_dict[k.lower().replace(' ', '_')] = k
    variables["labels_minimal_to_labels_dict"] = labels_minimal_to_labels_dict


def get_user_labels(current_labels: List[str] = None):
    try:
        enable_custom_labels = get_settings().config.get('enable_custom_labels', False)
        custom_labels = get_settings().get('custom_labels', [])
        if current_labels is None:
            current_labels = []
        user_labels = []
        for label in current_labels:
            if label.lower() in ['bug fix', 'tests', 'enhancement', 'documentation', 'other']:
                continue
            if enable_custom_labels:
                if label in custom_labels:
                    continue
            user_labels.append(label)
        if user_labels:
            get_logger().debug(f"Keeping user labels: {user_labels}")
    except Exception as e:
        get_logger().exception(f"Failed to get user labels: {e}")
        return current_labels
    return user_labels


def github_action_output(output_data: dict, key_name: str):
    try:
        if not get_settings().get('github_action_config.enable_output', False):
            return

        key_data = output_data.get(key_name, {})
        with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
            print(f"{key_name}={json.dumps(key_data, indent=None, ensure_ascii=False)}", file=fh)
    except Exception as e:
        get_logger().error(f"Failed to write to GitHub Action output: {e}")


def show_relevant_configurations(relevant_section: str) -> str:
    skip_keys = ['ai_disclaimer', 'ai_disclaimer_title', 'ANALYTICS_FOLDER', 'secret_provider', 'skip_keys', 'app_id', 'redirect',
                 'trial_prefix_message', 'no_eligible_message', 'identity_provider', 'ALLOWED_REPOS', 'APP_NAME']
    extra_skip_keys = get_settings().config.get('config.skip_keys', [])
    if extra_skip_keys:
        skip_keys.extend(extra_skip_keys)

    markdown_text = ""
    markdown_text += "\n<hr>\n<details> <summary><strong>🛠️ Relevant configurations:</strong></summary> \n\n"
    markdown_text += "<br>These are the relevant [configurations](https://github.com/khulnasoft/pr-insight/blob/main/pr_insight/settings/configuration.toml) for this tool:\n\n"
    markdown_text += f"**[config**]\n```yaml\n\n"
    for key, value in get_settings().config.items():
        if key in skip_keys:
            continue
        markdown_text += f"{key}: {value}\n"
    markdown_text += "\n```\n"
    markdown_text += f"\n**[{relevant_section}]**\n```yaml\n\n"
    for key, value in get_settings().get(relevant_section, {}).items():
        if key in skip_keys:
            continue
        markdown_text += f"{key}: {value}\n"
    markdown_text += "\n```"
    markdown_text += "\n</details>\n"
    return markdown_text


def is_value_no(value):
    if not value:
        return True
    value_str = str(value).strip().lower()
    return value_str in ['no', 'none', 'false']


def set_pr_string(repo_name, pr_number):
    return f"{repo_name}#{pr_number}"


def string_to_uniform_number(s: str) -> float:
    hash_object = hashlib.sha256(s.encode())
    hash_int = int(hash_object.hexdigest(), 16)
    max_hash_int = 2 ** 256 - 1
    return float(hash_int) / max_hash_int


def process_description(description_full: str) -> tuple[str, list]:
    if not description_full:
        return "", []

    if PRDescriptionHeader.FILE_WALKTHROUGH.value in description_full:
        try:
            regex_pattern = r'<details.*?>\s*<summary>\s*<h3>\s*' + re.escape(PRDescriptionHeader.FILE_WALKTHROUGH.value) + r'\s*</h3>\s*</summary>'
            description_split = re.split(regex_pattern, description_full, maxsplit=1, flags=re.DOTALL)
            if len(description_split) == 1:
                get_logger().debug("Could not find regex pattern for file walkthrough, falling back to simple split")
                description_split = description_full.split(PRDescriptionHeader.FILE_WALKTHROUGH.value, 1)
        except Exception as e:
            get_logger().warning(f"Failed to split description using regex, falling back to simple split: {e}")
            description_split = description_full.split(PRDescriptionHeader.FILE_WALKTHROUGH.value, 1)

        if len(description_split) < 2:
            get_logger().error("Failed to split description into base and changes walkthrough", artifact={'description': description_full})
            return description_full.strip(), []

        base_description_str = description_split[0].strip()
        changes_walkthrough_str = description_split[1] if len(description_split) > 1 else ""
    else:
        return description_full.strip(), []

    try:
        if changes_walkthrough_str:
            if '</table>\n\n___' in changes_walkthrough_str:
                end = changes_walkthrough_str.index("</table>\n\n___")
            elif '\n___' in changes_walkthrough_str:
                end = changes_walkthrough_str.index("\n___")
            else:
                end = len(changes_walkthrough_str)
            changes_walkthrough_str = changes_walkthrough_str[:end]

            h = html2text.HTML2Text()
            h.body_width = 0

            pattern = r'<tr>\s*<td>\s*(<details>\s*<summary>(.*?)</summary>(.*?)</details>)\s*</td>'
            files_found = re.findall(pattern, changes_walkthrough_str, re.DOTALL)
            files = []
            for file_data in files_found:
                try:
                    if isinstance(file_data, tuple):
                        file_data = file_data[0]
                    pattern = r'<details>\s*<summary><strong>(.*?)</strong>\s*<dd><code>(.*?)</code>.*?</summary>\s*<hr>\s*(.*?)\s*(?:<li>|•)(.*?)</details>'
                    res = re.search(pattern, file_data, re.DOTALL)
                    if not res or res.lastindex != 4:
                        pattern_back = r'<details>\s*<summary><strong>(.*?)</strong><dd><code>(.*?)</code>.*?</summary>\s*<hr>\s*(.*?)\n\n\s*(.*?)</details>'
                        res = re.search(pattern_back, file_data, re.DOTALL)
                    if not res or res.lastindex != 4:
                        pattern_back = r'<details>\s*<summary><strong>(.*?)</strong>\s*<dd><code>(.*?)</code>.*?</summary>\s*<hr>\s*(.*?)\s*-\s*(.*?)\s*</details>'
                        res = re.search(pattern_back, file_data, re.DOTALL)
                    if res and res.lastindex == 4:
                        short_filename = res.group(1).strip()
                        short_summary = res.group(2).strip()
                        long_filename = res.group(3).strip()
                        if long_filename.endswith('<ul>'):
                            long_filename = long_filename[:-4].strip()
                        long_summary = res.group(4).strip()
                        long_summary = long_summary.replace('<br> *', '\n*').replace('<br>','').replace('\n','<br>')
                        long_summary = h.handle(long_summary).strip()
                        if long_summary.startswith('\\-'):
                            long_summary = "* " + long_summary[2:]
                        elif not long_summary.startswith('*'):
                            long_summary = f"* {long_summary}"

                        files.append({
                            'short_file_name': short_filename,
                            'full_file_name': long_filename,
                            'short_summary': short_summary,
                            'long_summary': long_summary
                        })
                    else:
                        if '<code>...</code>' in file_data:
                            pass
                        else:
                            get_logger().warning(f"Failed to parse description", artifact={'description': file_data})
                except Exception as e:
                    get_logger().exception(f"Failed to process description: {e}", artifact={'description': file_data})
    except Exception as e:
        get_logger().exception(f"Failed to process description: {e}")

    return base_description_str, files


def get_version() -> str:
    if os.path.exists("pyproject.toml"):
        if sys.version_info >= (3, 11):
            import tomllib
            with open("pyproject.toml", "rb") as f:
                data = tomllib.load(f)
                if "project" in data and "version" in data["project"]:
                    return data["project"]["version"]
                else:
                    get_logger().warning("Version not found in pyproject.toml")
        else:
            get_logger().warning("Unable to determine local version from pyproject.toml")

    try:
        return version('pr-insight')
    except PackageNotFoundError:
        get_logger().warning("Unable to find package named 'pr-insight'")
        return "unknown"
