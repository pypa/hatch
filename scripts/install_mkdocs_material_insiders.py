import os
import subprocess
import sys

TOKEN = os.environ.get('GH_TOKEN_MKDOCS_MATERIAL_INSIDERS', '')
DEP_REF = f'git+https://{TOKEN}@github.com/squidfunk/mkdocs-material-insiders.git'
GIT_REF = '2ab4dc8ce4f249164ac1d8d3e46a12c5c0b71230'


def main():
    if not TOKEN:
        print('No token is set, skipping')
        return

    dependency = f'mkdocs-material[imaging] @ {DEP_REF}@{GIT_REF}'
    try:
        process = subprocess.Popen(
            ['uv', 'pip', 'install', dependency],  # noqa: S607
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding='utf-8',
        )
    except Exception as e:  # noqa: BLE001
        print(str(e).replace(TOKEN, '*****'))
        sys.exit(1)

    with process:
        for line in iter(process.stdout.readline, ''):
            print(line.replace(TOKEN, '*****'), end='')

    sys.exit(process.returncode)


if __name__ == '__main__':
    main()
