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
            Path(kwargs['package_name'], '__init__.py'),
            f"""\
# SPDX-FileCopyrightText: {kwargs['year']}-present {kwargs['author']} <{kwargs['email']}>
#
# SPDX-License-Identifier: MIT
""",
        ),
        File(
            Path(kwargs['package_name'], '__about__.py'),
            f"""\
# SPDX-FileCopyrightText: {kwargs['year']}-present {kwargs['author']} <{kwargs['email']}>
#
# SPDX-License-Identifier: MIT
__version__ = '0.0.1'
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
description = ''
readme = "README.md"
requires-python = ">=3.7"
license = "MIT"
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
  "Programming Language :: Python :: Implementation :: CPython",
  "Programming Language :: Python :: Implementation :: PyPy",
]
dependencies = []
dynamic = ["version"]

[project.urls]

[tool.hatch.version]
path = "{kwargs['package_name']}/__about__.py"

[tool.hatch.build.targets.sdist]
[tool.hatch.build.targets.wheel]

[tool.hatch.envs.default]
dependencies = [
  "pytest",
  "pytest-cov",
]
[tool.hatch.envs.default.scripts]
cov = "pytest --cov-report=term-missing --cov-config=pyproject.toml --cov={kwargs['package_name']} --cov=tests"
no-cov = "cov --no-cov"

[[tool.hatch.envs.test.matrix]]
python = ["37", "38", "39", "310"]

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
