from ..utils.fs import Path
from . import File


class CommandLinePackage(File):
    TEMPLATE = """\
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
        python-version: ['3.7', '3.8', '3.9', '3.10']

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install Hatch
      run: pip install --upgrade hatch

    - name: Run tests
      run: hatch run cov
"""  # noqa: E501

    def __init__(self, template_config: dict, plugin_config: dict):
        super().__init__(Path('.github', 'workflows', 'test.yml'), self.TEMPLATE)
