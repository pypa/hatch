import argparse
import re
import subprocess
from datetime import datetime, timezone

from utils import ROOT, get_latest_release

TEMPLATE = (
    '## [{version}](https://github.com/pypa/hatch/releases/tag/{project}-v{version}) - '
    '{year}-{month:02}-{day:02} ## {{: #{project}-v{version} }}'
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('project', choices=['hatch', 'hatchling'])
    parser.add_argument('version')
    args = parser.parse_args()

    root_dir = project_dir = ROOT
    if args.project == 'hatchling':
        project_dir = root_dir / 'backend'

    history_file = root_dir / 'docs' / 'history' / f'{args.project}.md'

    if args.project == 'hatchling':
        process = subprocess.run(  # noqa: PLW1510
            ['hatch', 'version', args.version],  # noqa: S607
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding='utf-8',
            cwd=str(project_dir),
        )
        if process.returncode:
            raise OSError(process.stdout)

        new_version = re.search(r'New: (.+)$', process.stdout, re.MULTILINE).group(1)
    else:
        from hatchling.version.scheme.standard import StandardScheme

        latest_version, _ = get_latest_release(args.project)

        scheme = StandardScheme(str(project_dir), {})
        new_version = scheme.update(args.version, latest_version, {})

    now = datetime.now(timezone.utc)

    history_file_lines = history_file.read_text(encoding='utf-8').splitlines()
    insertion_index = history_file_lines.index('## Unreleased') + 1
    history_file_lines.insert(
        insertion_index,
        TEMPLATE.format(project=args.project, version=new_version, year=now.year, month=now.month, day=now.day),
    )
    history_file_lines.insert(insertion_index, '')
    history_file_lines.append('')
    history_file.write_text('\n'.join(history_file_lines), encoding='utf-8')

    for command in (
        ['git', 'add', '--all'],
        ['git', 'commit', '-m', f'release {args.project.capitalize()} v{new_version}'],
    ):
        subprocess.run(command, check=True)


if __name__ == '__main__':
    main()
