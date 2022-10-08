import os
import shutil
import subprocess
import sys

TOKEN = os.environ.get('GH_TOKEN_MKDOCS_MATERIAL_INSIDERS', '')
DEP_REF = f'git+https://{TOKEN}@github.com/squidfunk/mkdocs-material-insiders.git'
GIT_REF = '2203a968f9992578460add59056b480ea454ddb3'


def main():
    if not TOKEN:
        print('No token is set, skipping')
        return

    python = shutil.which('python')
    try:
        process = subprocess.Popen(
            [python, '-m', 'pip', 'install', '--disable-pip-version-check', f'mkdocs-material @ {DEP_REF}@{GIT_REF}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding='utf-8',
        )
    except Exception as e:
        print(str(e).replace(TOKEN, '*****'))
        sys.exit(1)

    with process:
        for line in iter(process.stdout.readline, ''):
            print(line.replace(TOKEN, '*****'), end='')

    sys.exit(process.returncode)


if __name__ == '__main__':
    main()
