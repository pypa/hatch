import argparse
import re
import webbrowser
from pathlib import Path
from urllib.parse import urlencode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('project', choices=['hatch', 'hatchling'])
    args = parser.parse_args()

    history_file = Path.cwd() / 'docs' / 'history' / f'{args.project}.md'

    release_headers = 0
    history_file_lines = []
    with history_file.open(encoding='utf-8') as f:
        for line in f:
            history_file_lines.append(line.rstrip())

            if line.startswith('## '):
                release_headers += 1

            if release_headers == 3:
                break

    release_lines = history_file_lines[history_file_lines.index('## Unreleased') + 1 : -1]
    while True:
        release_header = release_lines.pop(0)
        if release_header.startswith('## '):
            break

    version = re.search(r'\[(.+)\]', release_header).group(1)

    params = urlencode(
        {
            'title': f'{args.project.capitalize()} v{version}',
            'tag': f'{args.project}-v{version}',
            'body': '\n'.join(release_lines).strip(),
        }
    )

    url = f'https://github.com/pypa/hatch/releases/new?{params}'
    webbrowser.open_new_tab(url)


if __name__ == '__main__':
    main()
