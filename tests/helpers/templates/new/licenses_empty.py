from hatch.template import File
from hatch.utils.fs import Path


def get_files(**kwargs):
    return [
        File(Path('src', kwargs['package_name'], '__init__.py')),
        File(Path('src', kwargs['package_name'], '__about__.py'), '__version__ = "0.0.1"\n'),
        File(Path('tests', '__init__.py')),
        File(
            Path('README.md'),
            f"""\
# {kwargs['project_name']}

[![PyPI - Version](https://img.shields.io/pypi/v/{kwargs['project_name_normalized']}.svg)](https://pypi.org/project/{kwargs['project_name_normalized']})
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/{kwargs['project_name_normalized']}.svg)](https://pypi.org/project/{kwargs['project_name_normalized']})

-----

**Table of Contents**

- [Installation](#installation)

## Installation

```console
pip install {kwargs['project_name_normalized']}
```
""",  # noqa: E501
        ),
        File(
            Path('pyproject.toml'),
            f"""\
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{kwargs['project_name_normalized']}"
dynamic = ["version"]
description = ''
readme = "README.md"
requires-python = ">=3.7"
license = ""
keywords = []
authors = [
  {{ name = "{kwargs['author']}", email = "{kwargs['email']}" }},
]
classifiers = [
  "Development Status :: 4 - Beta",
  "Programming Language :: Python",
  "Programming Language :: Python :: 3.7",
  "Programming Language :: Python :: 3.8",
  "Programming Language :: Python :: 3.9",
  "Programming Language :: Python :: 3.10",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: Implementation :: CPython",
  "Programming Language :: Python :: Implementation :: PyPy",
]
dependencies = []

[project.urls]
Documentation = "https://github.com/unknown/{kwargs['project_name_normalized']}#readme"
Issues = "https://github.com/unknown/{kwargs['project_name_normalized']}/issues"
Source = "https://github.com/unknown/{kwargs['project_name_normalized']}"

[tool.hatch.version]
path = "src/{kwargs['package_name']}/__about__.py"

[tool.hatch.envs.default]
dependencies = [
  "pytest",
  "pytest-cov",
]
[tool.hatch.envs.default.scripts]
test = "pytest --no-cov {{args:tests}}"
test-cov = "pytest --cov --cov-report=term-missing --cov-config=pyproject.toml {{args:tests}}"

[[tool.hatch.envs.all.matrix]]
python = ["3.7", "3.8", "3.9", "3.10", "3.11"]

[tool.hatch.envs.lint]
detached = true
dependencies = [
  "black",
  "mypy",
  "ruff",
]
[tool.hatch.envs.lint.scripts]
typing = "mypy --install-types --non-interactive {{args:src/{kwargs['package_name']} tests}}"
style = [
  "ruff {{args:.}}",
  "black --check --diff {{args:.}}",
]
fmt = [
  "black {{args:.}}",
  "ruff --fix {{args:.}}",
  "style",
]
all = [
  "style",
  "typing",
]

[tool.black]
target-version = ["py37"]
line-length = 120
skip-string-normalization = true

[tool.ruff]
target-version = "py37"
line-length = 120
select = ["A", "B", "C", "E", "F", "FBT", "I", "M", "N", "Q", "RUF", "S", "T", "U", "W", "YTT"]
ignore = [
  # Allow non-abstract empty methods in abstract base classes
  "B027",
  # Ignore McCabe complexity
  "C901",
  # Allow boolean positional values in function calls, like `dict.get(... True)`
  "FBT003",
  # Ignore checks for possible passwords
  "S105", "S106", "S107",
]
unfixable = [
  # Don't touch unused imports
  "F401",
]

[tool.ruff.isort]
known-first-party = ["{kwargs['package_name']}"]

[tool.ruff.flake8-tidy-imports]
ban-relative-imports = "all"

[tool.ruff.per-file-ignores]
# Tests can use relative imports and assertions
"tests/**/*" = ["I252", "S101"]

[tool.coverage.run]
source_pkgs = ["{kwargs['package_name']}", "tests"]
branch = true
parallel = true
omit = [
  "src/{kwargs['package_name']}/__about__.py",
]

[tool.coverage.paths]
{kwargs['package_name']} = ["src/{kwargs['package_name']}", "*/{kwargs['project_name_normalized']}/src/{kwargs['package_name']}"]
tests = ["tests", "*/{kwargs['project_name_normalized']}/tests"]

[tool.coverage.report]
exclude_lines = [
  "no cov",
  "if __name__ == .__main__.:",
  "if TYPE_CHECKING:",
]
""",  # noqa: E501
        ),
    ]
