import os
import subprocess
from collections import defaultdict
from decimal import ROUND_DOWN, Decimal
from pathlib import Path

PRECISION = Decimal('.01')
PACKAGES = {
    f'backend{os.sep}src{os.sep}hatchling{os.sep}': 'hatchling',
    f'src{os.sep}hatch{os.sep}': 'hatch',
    f'tests{os.sep}': 'tests',
}


def main():
    project_root = Path(__file__).resolve().parent.parent
    coverage_file = project_root / 'coverage.md'

    report = subprocess.check_output(
        ['coverage', 'report', '--precision', str(abs(PRECISION.adjusted()))],
        encoding='utf-8',
    )

    packages = defaultdict(lambda: {'hits': 0, 'misses': 0})
    for line in report.strip().splitlines()[2:-2]:
        # Split from the right one less than the number of columns in case filenames contain spaces
        parts = line.rsplit(maxsplit=5)
        if len(parts) != 6:
            raise ValueError('unable to parse coverage')

        module, hits, misses = parts[:3]
        for relative_path, package in PACKAGES.items():
            if module.startswith(relative_path):
                data = packages[package]
                data['hits'] += int(hits)
                data['misses'] += int(misses)
                break
        else:
            raise ValueError(f'unknown package: {module}')

    lines = [
        '\n',
        'Package | Statements\n',
        '--- | ---\n',
    ]
    total_hits = 0
    total_misses = 0

    for package, data in sorted(packages.items()):
        hits = data['hits']
        misses = data['misses']
        total_hits += hits
        total_misses += misses
        statements = hits + misses

        rate = Decimal(hits) / Decimal(statements) * 100
        rate = rate.quantize(PRECISION, rounding=ROUND_DOWN)
        lines.append(f'{package} | {100 if rate == 100 else rate}% ({hits} / {statements})\n')

    total_statements = total_hits + total_misses
    total_rate = Decimal(total_hits) / Decimal(total_statements) * 100
    total_rate = rate.quantize(PRECISION, rounding=ROUND_DOWN)
    color = 'ok' if float(total_rate) >= 95 else 'critical'
    lines.insert(0, f'![Code Coverage](https://img.shields.io/badge/coverage-{total_rate}%25-{color}?style=flat)\n')

    lines.append(f'**Summary** | {100 if total_rate == 100 else total_rate}% ({total_hits} / {total_statements})\n')

    with coverage_file.open('w', encoding='utf-8') as f:
        f.write(''.join(lines))


if __name__ == '__main__':
    main()
