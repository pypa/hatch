from hatch.template import File
from hatch.utils.fs import Path

from .default import get_files as get_template_files


def get_files(**kwargs):
    files = []
    for f in get_template_files(**kwargs):
        files.append(File(Path(f.path), f.contents))

    files.append(
        File(
            Path('.github', 'workflows', 'test.yml'),
            """\
name: test

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

concurrency:
  group: test-${{ github.head_ref }}
  cancel-in-progress: true

env:
  PYTHONUNBUFFERED: "1"
  FORCE_COLOR: "1"

jobs:
  run:
    name: Python ${{ matrix.python-version }} on ${{ startsWith(matrix.os, 'macos-') && 'macOS' || startsWith(matrix.os, 'windows-') && 'Windows' || 'Linux' }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.7', '3.8', '3.9', '3.10', '3.11.0-beta.5 - 3.11']

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install Hatch
      run: pip install --upgrade hatch

    - name: Run tests
      run: hatch run cov
""",  # noqa: E501
        )
    )

    return files
