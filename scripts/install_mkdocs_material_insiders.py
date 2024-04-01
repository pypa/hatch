import os
import shutil
import subprocess
import sys

TOKEN = os.environ.get('GH_TOKEN_MKDOCS_MATERIAL_INSIDERS', '')
DEP_REF = f'git+https://{TOKEN}@github.com/squidfunk/mkdocs-material-insiders.git'
GIT_REF = '5ea838ccf4ac5085dc42cf1fbabe52c18653e8a6'


def main():
    if not TOKEN:
        print('No token is set, skipping')
        return

    python = shutil.which('python')
    dependency = f'mkdocs-material[imaging] @ {DEP_REF}@{GIT_REF}'
    try:
        process = subprocess.Popen(
            [python, '-m', 'pip', 'install', '--disable-pip-version-check', dependency],
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
