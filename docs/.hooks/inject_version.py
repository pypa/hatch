import os
import subprocess
from functools import cache

MARKER = '<HATCH_LATEST_VERSION>'
SEMVER_PARTS = 3

# Ignore the current documentation environment so that the version
# command can execute as usual in the default build environment
os.environ.pop('HATCH_ENV_ACTIVE', None)


@cache
def get_latest_version():
    output = subprocess.check_output(['hatch', '--no-color', 'version']).decode('utf-8').strip()  # noqa: S607

    version = output.replace('dev', '')
    parts = list(map(int, version.split('.')))
    major, minor, patch = parts[:SEMVER_PARTS]
    if len(parts) > SEMVER_PARTS:
        patch -= 1

    return f'{major}.{minor}.{patch}'


def on_page_read_source(
    page,
    config,  # noqa: ARG001
):
    with open(page.file.abs_src_path, encoding='utf-8') as f:
        return f.read().replace(MARKER, get_latest_version())
