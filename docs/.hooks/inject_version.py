import os
import subprocess
from functools import cache

from markdown.preprocessors import Preprocessor

MARKER = '<HATCH_LATEST_VERSION>'
SEMVER_PARTS = 3


@cache
def get_latest_version():
    env = dict(os.environ)
    # Ignore the current documentation environment so that the version
    # command can execute as usual in the default build environment
    env.pop('HATCH_ENV_ACTIVE', None)

    output = subprocess.check_output(['hatch', '--no-color', 'version'], env=env).decode('utf-8').strip()  # noqa: S607

    version = output.replace('dev', '')
    parts = list(map(int, version.split('.')))
    major, minor, patch = parts[:SEMVER_PARTS]
    if len(parts) > SEMVER_PARTS:
        patch -= 1

    return f'{major}.{minor}.{patch}'


class VersionInjectionPreprocessor(Preprocessor):
    def run(self, lines):  # noqa: PLR6301
        for i, line in enumerate(lines):
            lines[i] = line.replace(MARKER, get_latest_version())

        return lines
