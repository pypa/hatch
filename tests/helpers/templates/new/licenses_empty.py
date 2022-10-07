from hatch.template import File
from hatch.utils.fs import Path


def get_files(**kwargs):
    return [
        File(Path(kwargs['package_name'], '__init__.py')),
        File(Path(kwargs['package_name'], '__about__.py'), "__version__ = '0.0.1'\n"),
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
dynamic = ["version"]

[project.urls]
Documentation = "https://github.com/unknown/{kwargs['project_name_normalized']}#readme"
Issues = "https://github.com/unknown/{kwargs['project_name_normalized']}/issues"
Source = "https://github.com/unknown/{kwargs['project_name_normalized']}"

[tool.hatch.version]
path = "{kwargs['package_name']}/__about__.py"

[tool.hatch.envs.default]
dependencies = [
  "pytest",
  "pytest-cov",
]
[tool.hatch.envs.default.scripts]
cov = "pytest --cov-report=term-missing --cov-config=pyproject.toml --cov={kwargs['package_name']} --cov=tests {{args}}"
no-cov = "cov --no-cov {{args}}"

[[tool.hatch.envs.test.matrix]]
python = ["37", "38", "39", "310", "311"]

[tool.coverage.run]
branch = true
parallel = true
omit = [
  "{kwargs['package_name']}/__about__.py",
]

[tool.coverage.report]
exclude_lines = [
  "no cov",
  "if __name__ == .__main__.:",
  "if TYPE_CHECKING:",
]
""",
        ),
    ]  # noqa: E501
