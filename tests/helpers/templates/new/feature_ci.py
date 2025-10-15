from hatch.template import File
from hatch.utils.fs import Path

from .default import get_files as get_template_files


def get_files(**kwargs):
    files = [File(Path(f.path), f.contents) for f in get_template_files(**kwargs)]
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
        python-version: ['3.9', '3.10', '3.11', '3.12', '3.13', '3.14']

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install Hatch
      run: pip install --upgrade hatch

    - name: Run static analysis
      run: hatch fmt --check

    - name: Run tests
      run: hatch test --python ${{ matrix.python-version }} --cover --randomize --parallel --retries 2 --retry-delay 1
""",
        )
    )

    return files
