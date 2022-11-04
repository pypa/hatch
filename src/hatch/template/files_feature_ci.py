from hatch.template import File
from hatch.utils.fs import Path


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
        python-version: ['3.7', '3.8', '3.9', '3.10', '3.11']

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - uses: actions/cache@v3
      id: cache
      if: runner.os != 'Windows'
      with:
        path: ${{ env.pythonLocation }}
        key: ${{ runner.os }}-python-${{ env.pythonLocation }}-${{ hashFiles('pyproject.toml') }}-test-v02

    - name: Install Hatch
      if: steps.cache.outputs.cache-hit != 'true'
      run: pip install --upgrade hatch

    - name: Set the env directory
      run: hatch config set dirs.env.virtual ${{ env.pythonLocation }}/.envs

    - name: Create env
      if: steps.cache.outputs.cache-hit != 'true'
      run: hatch env create

    - name: Run tests
      run: hatch run cov
"""  # noqa: E501

    def __init__(self, template_config: dict, plugin_config: dict):
        super().__init__(Path('.github', 'workflows', 'test.yml'), self.TEMPLATE)
