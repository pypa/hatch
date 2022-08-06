# Testing builds

-----

For testing [Hatchling plugins](../../plugins/about.md#hatchling), you'll usually want to generate a project to execute builds as a real user would. For example, as a minimal [pytest](https://github.com/pytest-dev/pytest) fixture:

```python
from pathlib import Path

import pytest


@pytest.fixture
def new_project(tmp_path):
    project_dir = tmp_path / 'my-app'
    project_dir.mkdir()

    project_file = project_dir / 'pyproject.toml'
    project_file.write_text(
        f"""\
[build-system]
requires = ["hatchling", "hatch-plugin-name @ {Path.cwd().as_uri()}"]
build-backend = "hatchling.build"

[project]
name = "my-app"
version = "0.1.0"
""",
        encoding='utf-8',
    )
    ...
```

The issue with this is that after the first test session, the project will be forever cached by pip based on the file path. Therefore, subsequent tests runs will never use updated code.

To invalidate the cache, copy your code to a new path for every test session:

```python
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


@pytest.fixture(scope='session')
def plugin_dir():
    with TemporaryDirectory() as d:
        directory = Path(d, 'plugin')
        shutil.copytree(
            Path.cwd(), directory, ignore=shutil.ignore_patterns('.git')
        )

        yield directory.resolve()


@pytest.fixture
def new_project(tmp_path, plugin_dir):
    project_dir = tmp_path / 'my-app'
    project_dir.mkdir()

    project_file = project_dir / 'pyproject.toml'
    project_file.write_text(
        f"""\
[build-system]
requires = ["hatchling", "hatch-plugin-name @ {plugin_dir.as_uri()}"]
build-backend = "hatchling.build"

[project]
name = "my-app"
version = "0.1.0"
""",
        encoding='utf-8',
    )
    ...
```

!!! note
    This example chooses to ignore copying `.git` for performance reasons. You may want to ignore more patterns, or copy only specific paths like [this plugin](https://github.com/hynek/hatch-fancy-pypi-readme/blob/main/tests/conftest.py) does.
