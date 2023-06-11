import re
import sys

from utils import ROOT

HEADER_PATTERN = (
    r'^\[([a-z0-9.]+)\]\(https://github\.com/pypa/hatch/releases/tag/({package}-v\1)\)'
    r' - [0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}} ## \{{: #\2 \}}$'
)


def main():
    for package in ('hatch', 'hatchling'):
        history_file = ROOT / 'docs' / 'history' / f'{package}.md'
        current_pattern = HEADER_PATTERN.format(package=package)

        with history_file.open('r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                elif line.startswith('## '):
                    _, _, header = line.partition(' ')
                    if header == 'Unreleased':
                        continue
                    elif not re.search(current_pattern, header):
                        print('Invalid header:')
                        print(header)
                        sys.exit(1)


if __name__ == '__main__':
    main()
