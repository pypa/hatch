from hatch.template import File
from hatch.utils.fs import Path

from ..licenses import MIT


def get_files(**kwargs):
    return [
        File(
            Path('LICENSE.txt'),
            MIT.replace('<year>', f"{kwargs['year']}-present", 1).replace(
                '<copyright holders>', f"{kwargs['author']} <{kwargs['email']}>", 1
            ),
        ),
        File(
            Path('src', kwargs['package_name'], '__init__.py'),
            f"""\
# SPDX-FileCopyrightText: {kwargs['year']}-present {kwargs['author']} <{kwargs['email']}>
#
# SPDX-License-Identifier: MIT
""",
        ),
        File(
            Path('src', kwargs['package_name'], '__about__.py'),
            f"""\
# SPDX-FileCopyrightText: {kwargs['year']}-present {kwargs['author']} <{kwargs['email']}>
#
# SPDX-License-Identifier: MIT
__version__ = "0.0.1"
""",
        ),
        File(
            Path('tests', '__init__.py'),
            f"""\
# SPDX-FileCopyrightText: {kwargs['year']}-present {kwargs['author']} <{kwargs['email']}>
#
# SPDX-License-Identifier: MIT
""",
        ),
        File(
            Path('README.md'),
            f"""\
# {kwargs['project_name']}

[![PyPI - Version](https://img.shields.io/pypi/v/{kwargs['project_name_normalized']}.svg)](https://pypi.org/project/{kwargs['project_name_normalized']})
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/{kwargs['project_name_normalized']}.svg)](https://pypi.org/project/{kwargs['project_name_normalized']})

-----

**Table of Contents**

- [Installation](#installation)
- [License](#license)

## Installation

```console
pip install {kwargs['project_name_normalized']}
```

## License

`{kwargs['project_name_normalized']}` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
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
requires-python = ">=3.8"
license = "MIT"
keywords = []
authors = [
  {{ name = "{kwargs['author']}", email = "{kwargs['email']}" }},
]
classifiers = [
  "Development Status :: 4 - Beta",
  "Programming Language :: Python",
  "Programming Language :: Python :: 3.8",
  "Programming Language :: Python :: 3.9",
  "Programming Language :: Python :: 3.10",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
  "Programming Language :: Python :: Implementation :: CPython",
  "Programming Language :: Python :: Implementation :: PyPy",
]
dependencies = []

[project.urls]
Documentation = "https://github.com/unknown/{kwargs['project_name_normalized']}#readme"
Source = "https://github.com/unknown/{kwargs['project_name_normalized']}"
"Bug Tracker" = "https://github.com/unknown/{kwargs['project_name_normalized']}/issues"

[tool.hatch.version]
path = "src/{kwargs['package_name']}/__about__.py"

[tool.hatch.envs.default]
dependencies = [
  "coverage[toml]>=6.5",
  "pytest",
]
[tool.hatch.envs.default.scripts]
test = "pytest {{args:tests}}"
test-cov = "coverage run -m pytest {{args:tests}}"
cov-report = [
  "- coverage combine",
  "coverage report",
]
cov = [
  "test-cov",
  "cov-report",
]

[[tool.hatch.envs.all.matrix]]
python = ["3.8", "3.9", "3.10", "3.11", "3.12"]

[tool.hatch.envs.types]
dependencies = [
  "mypy>=1.0.0",
]
[tool.hatch.envs.types.scripts]
check = "mypy --install-types --non-interactive {{args:src/{kwargs['package_name']} tests}}"

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
