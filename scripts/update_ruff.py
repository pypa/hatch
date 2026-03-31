from __future__ import annotations

import json
import re
import subprocess
import sys
import typing
from importlib.metadata import version

from utils import ROOT

if typing.TYPE_CHECKING:
    from pathlib import Path

# fmt: off
UNSELECTED_RULE_PATTERNS: list[str] = [
    # Allow non-abstract empty methods in abstract base classes
    'B027',
    # Allow boolean positional values in function calls, like `dict.get(... True)`
    'FBT003',
    # Ignore complexity
    'C901', 'PLR0904', 'PLR0911', 'PLR0912', 'PLR0913', 'PLR0914', 'PLR0915', 'PLR0916', 'PLR0917', 'PLR1702',
    # These are dependent on projects themselves
    'AIR\\d+', 'CPY\\d+', 'D\\d+', 'DJ\\d+', 'NPY\\d+', 'PD\\d+',
    # Many projects either don't have type annotations or it would take much effort to satisfy this
    'ANN\\d+',
    # Don't be too strict about TODOs as not everyone uses them the same way
    'FIX\\d+', 'TD001', 'TD002', 'TD003',
    # There are valid reasons to not use pathlib such as performance and import cost
    'PTH\\d+', 'FURB101', 'FURB103',
    # Conflicts with type checking
    'RET501', 'RET502',
    # Under review https://github.com/astral-sh/ruff/issues/8796
    'PT004', 'PT005',
    # Buggy https://github.com/astral-sh/ruff/issues/4845
    'ERA001',
    # Business logic relying on other programs has no choice but to use subprocess
    'S404',
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
    'COM812', 'COM819', 'D206', 'D300', 'E111', 'E114', 'E117', 'E301', 'E302', 'E303', 'E304', 'E305', 'E306', "E501", 'ISC001', 'ISC002', 'Q000', 'Q001', 'Q002', 'Q003', 'Q004', 'W191',
    # Conflicts with context formatting in dependencies
    'RUF200',
    # Currently broken
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


def get_lines_until(file_path: Path, marker: str) -> list[str]:
    lines = file_path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.startswith(marker):
            block_start = i
            break
    else:
        message = f"Could not find {marker}: {file_path.relative_to(ROOT)}"
        raise ValueError(message)

    del lines[block_start:]
    return lines


def main():
    process = subprocess.run(  # noqa: PLW1510
        [sys.executable, "-m", "ruff", "rule", "--all", "--output-format", "json"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        cwd=str(ROOT),
    )
    if process.returncode:
        raise OSError(process.stdout)

    data_file = ROOT / "src" / "hatch" / "cli" / "fmt" / "core.py"
    lines = get_lines_until(data_file, "STABLE_RULES")

    ignored_pattern = re.compile(f"^({'|'.join(UNSELECTED_RULE_PATTERNS)})$")
    # https://github.com/astral-sh/ruff/issues/9891#issuecomment-1951403651
    removed_pattern = re.compile(r"^\s*#+\s+(removed|removal)", flags=re.IGNORECASE | re.MULTILINE)

    stable_rules: set[str] = set()
    preview_rules: set[str] = set()
    unselected_rules: set[str] = set()
    for rule in json.loads(process.stdout):
        code = rule["code"]
        if ignored_pattern.match(code) or removed_pattern.search(rule["explanation"]):
            unselected_rules.add(code)
            continue

        if rule["preview"]:
            preview_rules.add(code)
        else:
            stable_rules.add(code)

    lines.append("STABLE_RULES: tuple[str, ...] = (")
    lines.extend(f"    {rule!r}," for rule in sorted(stable_rules))
    lines.append(")")

    lines.append("PREVIEW_RULES: tuple[str, ...] = (")
    lines.extend(f"    {rule!r}," for rule in sorted(preview_rules))
    lines.append(")")

    lines.append("PER_FILE_IGNORED_RULES: dict[str, list[str]] = {")
    for ignored_glob, ignored_rules in sorted(PER_FILE_IGNORED_RULES.items()):
        lines.append(f"    {ignored_glob!r}: [")
        lines.extend(f"        {rule!r}," for rule in sorted(ignored_rules))
        lines.append("    ],")
    lines.append("}")

    lines.append("")
    data_file.write_text("\n".join(lines), encoding="utf-8")

    version_file = ROOT / "src" / "hatch" / "env" / "internal" / "static_analysis.py"
    latest_version = version("ruff")
    version_file.write_text(
        re.sub(
            r"^(RUFF_DEFAULT_VERSION.+=.+\').+?(\')$",
            rf"\g<1>{latest_version}\g<2>",
            version_file.read_text(encoding="utf-8"),
            count=1,
            flags=re.MULTILINE,
        ),
        encoding="utf-8",
    )

    data_file = ROOT / "docs" / ".hooks" / "render_ruff_defaults.py"
    lines = get_lines_until(data_file, "UNSELECTED_RULES")

    lines.append("UNSELECTED_RULES: tuple[str, ...] = (")
    lines.extend(f"    {rule!r}," for rule in sorted(unselected_rules))
    lines.append(")")

    lines.append("")
    data_file.write_text("\n".join(lines), encoding="utf-8")

    print(f"Stable rules: {len(stable_rules)}")
    print(f"Preview rules: {len(preview_rules)}")
    print(f"Unselected rules: {len(unselected_rules)}")


if __name__ == "__main__":
    main()
