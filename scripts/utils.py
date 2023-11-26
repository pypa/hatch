import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def get_latest_release(project):
    history_file = ROOT / 'docs' / 'history' / f'{project}.md'

    release_headers = 0
    history_file_lines = []
    with history_file.open(encoding='utf-8') as f:
        for line in f:
            history_file_lines.append(line.rstrip())

            if line.startswith('## '):
                release_headers += 1

            if release_headers == 3:  # noqa: PLR2004
                break

    release_lines = history_file_lines[history_file_lines.index('## Unreleased') + 1 : -1]
    while True:
        release_header = release_lines.pop(0)
        if release_header.startswith('## '):
            break

    return re.search(r'\[(.+)\]', release_header).group(1), '\n'.join(release_lines).strip()
