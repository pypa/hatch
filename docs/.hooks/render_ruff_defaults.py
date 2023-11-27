from __future__ import annotations

import os
import re
from collections import defaultdict
from functools import cache

from markdown.preprocessors import Preprocessor

MARKER_VERSION = '<HATCH_RUFF_VERSION>'
MARKER_SELECTED_RULES = '<HATCH_RUFF_SELECTED_RULES>'
MARKER_PER_FILE_IGNORED_RULES = '<HATCH_RUFF_PER_FILE_IGNORED_RULES>'
RULE_URLS = {'S': 'https://docs.astral.sh/ruff/rules/#flake8-bandit-s'}


@cache
def ruff_data():
    generated_file = os.path.join(os.getcwd(), 'src', 'hatch', 'env', 'internal', 'fmt.py')
    with open(generated_file, encoding='utf-8') as f:
        lines = f.read().splitlines()

    for i, line in enumerate(lines):
        if line.startswith('RUFF_MINIMUM_VERSION'):
            block_start = i
            break
    else:
        message = f'Could not find RUFF_MINIMUM_VERSION in {generated_file}'
        raise RuntimeError(message)

    data = {}
    exec('\n'.join(lines[block_start:]), None, data)  # noqa: S102
    return data


@cache
def get_ruff_version():
    return ruff_data()['RUFF_MINIMUM_VERSION']


@cache
def get_selected_rules():
    selected_rules = defaultdict(list)
    separator = re.compile(r'^(\D+)(\d+)$')

    data = ruff_data()
    for rules, preview in ((data['STABLE_RULES'], False), (data['PREVIEW_RULES'], True)):
        for rule in rules:
            match = separator.search(rule)
            if match is None:
                message = f'Could not parse rule {rule}'
                raise RuntimeError(message)

            group, number = match.groups()
            selected_rules[group].append((number, preview))

    lines = []
    for group, rule_data in sorted(selected_rules.items()):
        rule_data.sort(key=lambda x: int(x[0]))

        parts = []
        for number, preview in rule_data:
            rule = f'{group}{number}'
            part = f'[{rule}](https://docs.astral.sh/ruff/rules/{rule})'
            if preview:
                part += '^P^'
            parts.append(part)

        lines.append(f'- {", ".join(parts)}')

    return '\n'.join(lines)


@cache
def get_per_file_ignored_rules():
    lines = []
    for glob, rules in sorted(ruff_data()['PER_FILE_IGNORED_RULES'].items()):
        parts = []
        for rule in rules:
            url = RULE_URLS.get(rule) or f'https://docs.astral.sh/ruff/rules/{rule}'
            parts.append(f'[{rule}]({url})')

        lines.append(f'- `{glob}`: {", ".join(parts)}')

    return '\n'.join(lines)


class RuffDefaultsPreprocessor(Preprocessor):
    def run(self, lines):  # noqa: PLR6301
        return (
            '\n'.join(lines)
            .replace(MARKER_VERSION, get_ruff_version())
            .replace(MARKER_SELECTED_RULES, get_selected_rules())
            .replace(MARKER_PER_FILE_IGNORED_RULES, get_per_file_ignored_rules())
            .splitlines()
        )
