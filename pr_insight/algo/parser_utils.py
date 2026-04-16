from __future__ import annotations

import copy
import json
import re
from typing import List

import yaml
from pr_insight.config_loader import get_settings
from pr_insight.log import get_logger


def try_fix_json(review, max_iter=10, code_suggestions=False):
    if review.endswith("}"):
        return fix_json_escape_char(review)

    data = {}
    if code_suggestions:
        closing_bracket = "]}"
    else:
        closing_bracket = "]}}"

    if (review.rfind("'Code feedback': [") > 0 or review.rfind('"Code feedback": [') > 0) or \
            (review.rfind("'Code suggestions': [") > 0 or review.rfind('"Code suggestions": [') > 0):
        last_code_suggestion_ind = [m.end() for m in re.finditer(r"\}\s*,", review)][-1] - 1
        valid_json = False
        iter_count = 0

        while last_code_suggestion_ind > 0 and not valid_json and iter_count < max_iter:
            try:
                data = json.loads(review[:last_code_suggestion_ind] + closing_bracket)
                valid_json = True
                review = review[:last_code_suggestion_ind].strip() + closing_bracket
            except json.decoder.JSONDecodeError:
                review = review[:last_code_suggestion_ind]
                last_code_suggestion_ind = [m.end() for m in re.finditer(r"\}\s*,", review)][-1] - 1
                iter_count += 1

        if not valid_json:
            get_logger().error("Unable to decode JSON response from AI")
            data = {}

    return data


def fix_json_escape_char(json_message=None):
    try:
        result = json.loads(json_message)
    except Exception as e:
        idx_to_replace = int(str(e).split(' ')[-1].replace(')', ''))
        json_message = list(json_message)
        json_message[idx_to_replace] = ' '
        new_message = ''.join(json_message)
        return fix_json_escape_char(json_message=new_message)
    return result


def _fix_key_value(key: str, value: str):
    key = key.strip().upper()
    value = value.strip()
    try:
        value = yaml.safe_load(value)
    except Exception as e:
        get_logger().debug(f"Failed to parse YAML for config override {key}={value}", exc_info=e)
    return key, value


def update_settings_from_args(args: List[str]) -> List[str]:
    other_args = []
    if args:
        for arg in args:
            arg = arg.strip()
            if arg.startswith('--'):
                arg = arg.strip('-').strip()
                vals = arg.split('=', 1)
                if len(vals) != 2:
                    if len(vals) > 2:
                        get_logger().error(f'Invalid argument format: {arg}')
                    other_args.append(arg)
                    continue
                key, value = _fix_key_value(*vals)
                get_settings().set(key, value)
                get_logger().info(f'Updated setting {key} to: "{value}"')
            else:
                other_args.append(arg)
    return other_args


def load_yaml(response_text: str, keys_fix_yaml: List[str] = [], first_key="", last_key="") -> dict:
    response_text_original = copy.deepcopy(response_text)
    response_text = response_text.strip('\n').removeprefix('yaml').removeprefix('```yaml').rstrip().removesuffix('```')
    try:
        data = yaml.safe_load(response_text)
    except Exception as e:
        get_logger().warning(f"Initial failure to parse AI prediction: {e}")
        data = try_fix_yaml(response_text, keys_fix_yaml=keys_fix_yaml, first_key=first_key, last_key=last_key,
                            response_text_original=response_text_original)
        if not data:
            get_logger().error(f"Failed to parse AI prediction after fallbacks",
                               artifact={'response_text': response_text})
        else:
            get_logger().info(f"Successfully parsed AI prediction after fallbacks",
                              artifact={'response_text': response_text})
    return data


def try_fix_yaml(response_text: str,
                 keys_fix_yaml: List[str] = [],
                 first_key="",
                 last_key="",
                 response_text_original="") -> dict:
    response_text_lines = response_text.split('\n')

    keys_yaml = ['relevant line:', 'suggestion content:', 'relevant file:', 'existing code:',
                 'improved code:', 'label:', 'why:', 'suggestion_summary:']
    keys_yaml = keys_yaml + keys_fix_yaml

    response_text_lines_copy = response_text_lines.copy()
    for i in range(0, len(response_text_lines_copy)):
        for key in keys_yaml:
            if key in response_text_lines_copy[i] and not '|' in response_text_lines_copy[i]:
                response_text_lines_copy[i] = response_text_lines_copy[i].replace(f'{key}',
                                                                                  f'{key} |\n        ')
    try:
        data = yaml.safe_load('\n'.join(response_text_lines_copy))
        get_logger().info(f"Successfully parsed AI prediction after adding |-\n")
        return data
    except:
        pass

    response_text_copy = copy.deepcopy(response_text)
    response_text_copy = response_text_copy.replace('|\n', '|2\n')
    try:
        data = yaml.safe_load(response_text_copy)
        get_logger().info(f"Successfully parsed AI prediction after replacing | with |2")
        return data
    except:
        pass

    response_text_lines_copy = copy.deepcopy(response_text_copy).split('\n')
    for i in range(0, len(response_text_lines_copy)):
        initial_space = len(response_text_lines_copy[i]) - len(response_text_lines_copy[i].lstrip())
        if initial_space == 2 and '|2' not in response_text_lines_copy[i] and '}' in response_text_lines_copy[i]:
            response_text_lines_copy[i] = '    ' + response_text_lines_copy[i].lstrip()
    try:
        data = yaml.safe_load('\n'.join(response_text_lines_copy))
        get_logger().info(f"Successfully parsed AI prediction after replacing | with |2 and adding spaces")
        return data
    except:
        pass

    snippet_pattern = r'```yaml([\s\S]*?)```(?=\s*$|")'
    snippet = re.search(snippet_pattern, '\n'.join(response_text_lines_copy))
    if not snippet:
        snippet = re.search(snippet_pattern, response_text_original)
    if snippet:
        snippet_text = snippet.group()
        try:
            data = yaml.safe_load(snippet_text.removeprefix('```yaml').rstrip('`'))
            get_logger().info(f"Successfully parsed AI prediction after extracting yaml snippet")
            return data
        except:
            pass

    response_text_copy = response_text.strip().rstrip().removeprefix('{').removesuffix('}').rstrip(':\n')
    try:
        data = yaml.safe_load(response_text_copy)
        get_logger().info(f"Successfully parsed AI prediction after removing curly brackets")
        return data
    except:
        pass

    if first_key and last_key:
        index_start = response_text.find(f"\n{first_key}:")
        if index_start == -1:
            index_start = response_text.find(f"{first_key}:")
        index_last_code = response_text.rfind(f"{last_key}:")
        index_end = response_text.find("\n\n", index_last_code)
        if index_end == -1:
            index_end = len(response_text)
        response_text_copy = response_text[index_start:index_end].strip().strip('```yaml').strip('`').strip()
        if response_text_copy:
            try:
                data = yaml.safe_load(response_text_copy)
                get_logger().info(f"Successfully parsed AI prediction after extracting yaml snippet")
                return data
            except:
                pass

    response_text_lines_copy = response_text_lines.copy()
    for i in range(0, len(response_text_lines_copy)):
        if response_text_lines_copy[i].startswith('+'):
            response_text_lines_copy[i] = ' ' + response_text_lines_copy[i][1:]
    try:
        data = yaml.safe_load('\n'.join(response_text_lines_copy))
        get_logger().info(f"Successfully parsed AI prediction after removing leading '+'")
        return data
    except:
        pass

    if '\t' in response_text:
        response_text_copy = copy.deepcopy(response_text)
        response_text_copy = response_text_copy.replace('\t', '    ')
        try:
            data = yaml.safe_load(response_text_copy)
            get_logger().info(f"Successfully parsed AI prediction after replacing tabs with spaces")
            return data
        except:
            pass

    response_text_copy = copy.deepcopy(response_text)
    response_text_copy_lines = response_text_copy.split('\n')
    start_line = -1
    improve_sections = ['existing_code:', 'improved_code:', 'response:', 'why:']
    describe_sections = ['description:', 'title:', 'changes_diagram:', 'pr_files:', 'pr_ticket:']
    for i, line in enumerate(response_text_copy_lines):
        line_stripped = line.rstrip()
        if any(key in line_stripped for key in (improve_sections+describe_sections)):
            start_line = i
        elif line_stripped.endswith(': |') or line_stripped.endswith(': |-') or line_stripped.endswith(': |2') or any(line_stripped.endswith(key) for key in keys_yaml):
            start_line = -1
        elif start_line != -1:
            response_text_copy_lines[i] = '    ' + line
    response_text_copy = '\n'.join(response_text_copy_lines)
    response_text_copy = response_text_copy.replace(' |\n', ' |2\n')
    try:
        data = yaml.safe_load(response_text_copy)
        get_logger().info(f"Successfully parsed AI prediction after adding indent for sections of code blocks")
        return data
    except:
        pass

    response_text_copy = copy.deepcopy(response_text)
    response_text_copy = response_text_copy.lstrip('|\n')
    try:
        data = yaml.safe_load(response_text_copy)
        get_logger().info(f"Successfully parsed AI prediction after removing pipe chars")
        return data
    except:
        pass

    encodings_to_try = ['latin-1', 'utf-16']
    for encoding in encodings_to_try:
        try:
            data = yaml.safe_load(response_text.encode(encoding).decode("utf-8"))
            if data:
                get_logger().info(f"Successfully parsed AI prediction after decoding with {encoding} encoding")
                return data
        except:
            pass

    return {}
