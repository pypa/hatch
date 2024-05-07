from __future__ import annotations

import os
import re
from collections import defaultdict
from functools import cache
from typing import Any

from markdown.preprocessors import Preprocessor

MARKER_VERSION = '<HATCH_RUFF_VERSION>'
MARKER_SELECTED_RULES = '<HATCH_RUFF_SELECTED_RULES>'
MARKER_UNSELECTED_RULES = '<HATCH_RUFF_UNSELECTED_RULES>'
MARKER_STABLE_RULES_COUNT = '<HATCH_RUFF_STABLE_RULES_COUNT>'
MARKER_PREVIEW_RULES_COUNT = '<HATCH_RUFF_PREVIEW_RULES_COUNT>'
MARKER_UNSELECTED_RULES_COUNT = '<HATCH_RUFF_UNSELECTED_RULES_COUNT>'
MARKER_PER_FILE_IGNORED_RULES = '<HATCH_RUFF_PER_FILE_IGNORED_RULES>'
RULE_URLS = {'S': 'https://docs.astral.sh/ruff/rules/#flake8-bandit-s'}


def read_constants(path: str, start: str) -> dict[str, Any]:
    with open(path, encoding='utf-8') as f:
        lines = f.read().splitlines()

    for i, line in enumerate(lines):
        if line.startswith(start):
            block_start = i
            break
    else:
        message = f'Could not find {start} in {path}'
        raise RuntimeError(message)

    data = {}
    exec('\n'.join(lines[block_start:]), None, data)  # noqa: S102
    return data


def parse_rules(rules: tuple[str, ...]) -> defaultdict[str, list[str]]:
    selected_rules: defaultdict[str, list[str]] = defaultdict(list)
    separator = re.compile(r'^(\D+)(\d+)$')

    for rule in rules:
        match = separator.search(rule)
        if match is None:
            message = f'Could not parse rule {rule}'
            raise RuntimeError(message)

        group, number = match.groups()
        selected_rules[group].append(number)

    return selected_rules


def construct_collapsed_markdown_rule_list(text: str, rules: defaultdict[str, list[str]]) -> str:
    preview_rule_set = set(ruff_data()['PREVIEW_RULES'])

    lines = [f'??? "{text}"']
    for group, numbers in sorted(rules.items()):
        numbers.sort(key=lambda x: int(x[0]))

        parts = []
        for number in numbers:
            rule = f'{group}{number}'
            part = f'[{rule}](https://docs.astral.sh/ruff/rules/{rule})'
            if f'{group}{number}' in preview_rule_set:
                part += '^P^'
            parts.append(part)

        lines.append(f'    - {", ".join(parts)}')

    return '\n'.join(lines)


@cache
def ruff_data():
    root = os.getcwd()
    data = {}
    for path, start in (
        (os.path.join(root, 'src', 'hatch', 'cli', 'fmt', 'core.py'), 'STABLE_RULES'),
        (os.path.join(root, 'src', 'hatch', 'env', 'internal', 'static_analysis.py'), 'RUFF_DEFAULT_VERSION'),
    ):
        data.update(read_constants(path, start))

    return data


@cache
def get_ruff_version():
    return ruff_data()['RUFF_DEFAULT_VERSION']


@cache
def get_stable_rules_count():
    return str(len(ruff_data()['STABLE_RULES']))


@cache
def get_preview_rules_count():
    return str(len(ruff_data()['PREVIEW_RULES']))


@cache
def get_unselected_rules_count():
    return str(len(UNSELECTED_RULES))


@cache
def get_selected_rules():
    data = ruff_data()
    rules = parse_rules(data['STABLE_RULES'])
    for group, numbers in parse_rules(data['PREVIEW_RULES']).items():
        rules[group].extend(numbers)

    return construct_collapsed_markdown_rule_list('Selected rules', rules)


@cache
def get_unselected_rules():
    return construct_collapsed_markdown_rule_list('Unselected rules', parse_rules(UNSELECTED_RULES))


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
            .replace(MARKER_STABLE_RULES_COUNT, get_stable_rules_count())
            .replace(MARKER_PREVIEW_RULES_COUNT, get_preview_rules_count())
            .replace(MARKER_UNSELECTED_RULES_COUNT, get_unselected_rules_count())
            .replace(MARKER_SELECTED_RULES, get_selected_rules())
            .replace(MARKER_UNSELECTED_RULES, get_unselected_rules())
            .replace(MARKER_PER_FILE_IGNORED_RULES, get_per_file_ignored_rules())
            .splitlines()
        )


UNSELECTED_RULES: tuple[str, ...] = (
    'AIR001',
    'ANN001',
    'ANN002',
    'ANN003',
    'ANN101',
    'ANN102',
    'ANN201',
    'ANN202',
    'ANN204',
    'ANN205',
    'ANN206',
    'ANN401',
    'B027',
    'C901',
    'COM812',
    'COM819',
    'CPY001',
    'D100',
    'D101',
    'D102',
    'D103',
    'D104',
    'D105',
    'D106',
    'D107',
    'D200',
    'D201',
    'D202',
    'D203',
    'D204',
    'D205',
    'D206',
    'D207',
    'D208',
    'D209',
    'D210',
    'D211',
    'D212',
    'D213',
    'D214',
    'D215',
    'D300',
    'D301',
    'D400',
    'D401',
    'D402',
    'D403',
    'D404',
    'D405',
    'D406',
    'D407',
    'D408',
    'D409',
    'D410',
    'D411',
    'D412',
    'D413',
    'D414',
    'D415',
    'D416',
    'D417',
    'D418',
    'D419',
    'DJ001',
    'DJ003',
    'DJ006',
    'DJ007',
    'DJ008',
    'DJ012',
    'DJ013',
    'E111',
    'E114',
    'E117',
    'E301',
    'E302',
    'E303',
    'E304',
    'E305',
    'E306',
    'E501',
    'ERA001',
    'FBT003',
    'FIX001',
    'FIX002',
    'FIX003',
    'FIX004',
    'FURB101',
    'FURB103',
    'FURB140',
    'ISC001',
    'ISC002',
    'NPY001',
    'NPY002',
    'NPY003',
    'NPY201',
    'PD002',
    'PD003',
    'PD004',
    'PD007',
    'PD008',
    'PD009',
    'PD010',
    'PD011',
    'PD012',
    'PD013',
    'PD015',
    'PD101',
    'PD901',
    'PERF203',
    'PGH001',
    'PGH002',
    'PGH003',
    'PGH004',
    'PLR0904',
    'PLR0911',
    'PLR0912',
    'PLR0913',
    'PLR0914',
    'PLR0915',
    'PLR0916',
    'PLR0917',
    'PLR1702',
    'PLR1706',
    'PT004',
    'PT005',
    'PTH100',
    'PTH101',
    'PTH102',
    'PTH103',
    'PTH104',
    'PTH105',
    'PTH106',
    'PTH107',
    'PTH108',
    'PTH109',
    'PTH110',
    'PTH111',
    'PTH112',
    'PTH113',
    'PTH114',
    'PTH115',
    'PTH116',
    'PTH117',
    'PTH118',
    'PTH119',
    'PTH120',
    'PTH121',
    'PTH122',
    'PTH123',
    'PTH124',
    'PTH201',
    'PTH202',
    'PTH203',
    'PTH204',
    'PTH205',
    'PTH206',
    'PTH207',
    'Q000',
    'Q001',
    'Q002',
    'Q003',
    'Q004',
    'RET501',
    'RET502',
    'RUF011',
    'RUF200',
    'S404',
    'S410',
    'S603',
    'SIM401',
    'TD001',
    'TD002',
    'TD003',
    'TRY200',
    'W191',
)
