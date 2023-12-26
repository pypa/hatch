from __future__ import annotations

import json
import re
import subprocess
import sys
from importlib.metadata import version

from utils import ROOT

# fmt: off
UNSELECTED_RULE_PATTERNS: list[str] = [
    # Allow non-abstract empty methods in abstract base classes
    'B027',
    # Allow boolean positional values in function calls, like `dict.get(... True)`
    'FBT003',
    # Ignore complexity
    'C901', 'PLR0904', 'PLR0911', 'PLR0912', 'PLR0913', 'PLR0914', 'PLR0915', 'PLR0916', 'PLR0917',
    # These are dependent on projects themselves
    'AIR\\d+', 'CPY\\d+', 'D\\d+', 'DJ\\d+', 'NPY\\d+', 'PD\\d+',
    # Many projects either don't have type annotations or it would take much effort to satisfy this
    'ANN\\d+',
    # Don't be too strict about TODOs as not everyone uses them the same way
    'FIX\\d+', 'TD001', 'TD002', 'TD003',
    # There are valid reasons to not use pathlib such as performance and import cost
    'PTH\\d+', 'FURB101',
    # Conflicts with type checking
    'RET501', 'RET502',
    # Under review https://github.com/astral-sh/ruff/issues/8796
    'PT004', 'PT005',
    # Buggy https://github.com/astral-sh/ruff/issues/4845
    'ERA001',
    # Too prone to false positives and might be removed https://github.com/astral-sh/ruff/issues/4045
    'S603',
    # Too prone to false positives https://github.com/astral-sh/ruff/issues/8761
    'SIM401',
    # Allow for easy ignores
    'PGH003', 'PGH004',
    # This is required sometimes, and doesn't matter on Python 3.11+
    'PERF203',
    # Potentially unnecessary on Python 3.12+
    'FURB140',
    # Conflicts with formatter, see:
    # https://docs.astral.sh/ruff/formatter/#conflicting-lint-rules
    'COM812', 'COM819', 'D206', 'D300', 'E111', 'E114', 'E117', 'ISC001', 'ISC002', 'Q000', 'Q001', 'Q002', 'Q003', 'Q004', 'W191',  # noqa: E501
]
PER_FILE_IGNORED_RULES: dict[str, list[str]] = {
    '**/scripts/*': [
        # Implicit namespace packages
        'INP001',
        # Print statements
        'T201',
    ],
    '**/tests/**/*': [
        # Empty string comparisons
        'PLC1901',
        # Magic values
        'PLR2004',
        # Methods that don't use `self`
        'PLR6301',
        # Potential security issues like assert statements and hardcoded passwords
        'S',
        # Relative imports
        'TID252',
    ],
}
# fmt: on


def main():
    process = subprocess.run(  # noqa: PLW1510
        [sys.executable, '-m', 'ruff', 'rule', '--all', '--output-format', 'json'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding='utf-8',
        cwd=str(ROOT),
    )
    if process.returncode:
        raise OSError(process.stdout)

    data_file = ROOT / 'src' / 'hatch' / 'cli' / 'fmt' / 'core.py'
    lines = data_file.read_text(encoding='utf-8').splitlines()
    for i, line in enumerate(lines):
        if line.startswith('STABLE_RULES'):
            block_start = i
            break
    else:
        message = 'Could not find STABLE_RULES'
        raise ValueError(message)

    del lines[block_start:]

    ignored_pattern = f'^({"|".join(UNSELECTED_RULE_PATTERNS)})$'
    stable_rules: set[str] = set()
    preview_rules: set[str] = set()
    for rule in json.loads(process.stdout):
        code = rule['code']
        if re.search(ignored_pattern, code):
            continue

        if rule['preview']:
            preview_rules.add(code)
        else:
            stable_rules.add(code)

    lines.append('STABLE_RULES: tuple[str, ...] = (')
    lines.extend(f'    {rule!r},' for rule in sorted(stable_rules))
    lines.append(')')

    lines.append('PREVIEW_RULES: tuple[str, ...] = (')
    lines.extend(f'    {rule!r},' for rule in sorted(preview_rules))
    lines.append(')')

    lines.append('PER_FILE_IGNORED_RULES: dict[str, list[str]] = {')
    for ignored_glob, ignored_rules in sorted(PER_FILE_IGNORED_RULES.items()):
        lines.append(f'    {ignored_glob!r}: [')
        lines.extend(f'        {rule!r},' for rule in sorted(ignored_rules))
        lines.append('    ],')
    lines.append('}')

    lines.append('')
    data_file.write_text('\n'.join(lines), encoding='utf-8')

    version_file = ROOT / 'src' / 'hatch' / 'env' / 'internal' / 'static_analysis.py'
    latest_version = version('ruff')
    version_file.write_text(
        re.sub(
            r'^(RUFF_DEFAULT_VERSION.+=.+\').+?(\')$',
            rf'\g<1>{latest_version}\g<2>',
            version_file.read_text(encoding='utf-8'),
            count=1,
            flags=re.MULTILINE,
        ),
        encoding='utf-8',
    )


if __name__ == '__main__':
    main()
