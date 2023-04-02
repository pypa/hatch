from hatch.template import File
from hatch.utils.fs import Path


class PackageRoot(File):
    def __init__(self, template_config: dict, plugin_config: dict):
        super().__init__(Path(template_config['package_name'], '__init__.py'), '')


class MetadataFile(File):
    def __init__(self, template_config: dict, plugin_config: dict):
        super().__init__(Path(template_config['package_name'], '__about__.py'), '__version__ = "0.0.1"\n')


class Readme(File):
    TEMPLATE = """\
# {project_name}

[![PyPI - Version](https://img.shields.io/pypi/v/{project_name_normalized}.svg)](https://pypi.org/project/{project_name_normalized})
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/{project_name_normalized}.svg)](https://pypi.org/project/{project_name_normalized})
{extra_badges}
-----

**Table of Contents**

- [Installation](#installation)
{extra_toc}
## Installation

```console
pip install {project_name_normalized}
```{license_info}
"""

    def __init__(self, template_config: dict, plugin_config: dict):
        extra_badges = ''
        extra_toc = ''

        license_info = ''
        if template_config['license_data']:
            extra_toc += '- [License](#license)\n'
            license_info += (
                f"\n\n## License\n\n`{template_config['project_name_normalized']}` is distributed under the terms of "
            )

            license_data = template_config['license_data']
            if len(license_data) == 1:
                license_id = list(license_data)[0]
                license_info += f'the [{license_id}](https://spdx.org/licenses/{license_id}.html) license.'
            else:
                license_info += 'any of the following licenses:\n'
                for license_id in sorted(license_data):
                    license_info += f'\n- [{license_id}](https://spdx.org/licenses/{license_id}.html)'

        super().__init__(
            Path(template_config['readme_file_path']),
            self.TEMPLATE.format(
                extra_badges=extra_badges, extra_toc=extra_toc, license_info=license_info, **template_config
            ),
        )


class PyProject(File):
    TEMPLATE = """\
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{project_name_normalized}"
dynamic = ["version"]
description = {description!r}
readme = "{readme_file_path}"
requires-python = ">=3.7"
license = "{license_expression}"{license_files}
keywords = []
authors = [
  {{ name = "{name}", email = "{email}" }},
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
dependencies = {dependency_data}

[project.urls]{project_url_data}{cli_scripts}

[tool.hatch.version]
path = "{package_metadata_file_path}"{tests_section}
"""

    def __init__(self, template_config: dict, plugin_config: dict):
        template_config = dict(template_config)
        template_config['name'] = repr(template_config['name'])[1:-1]

        project_url_data = ''
        project_urls = (
            plugin_config['project_urls']
            if 'project_urls' in plugin_config
            else {
                'Documentation': 'https://github.com/unknown/{project_name_normalized}#readme',
                'Issues': 'https://github.com/unknown/{project_name_normalized}/issues',
                'Source': 'https://github.com/unknown/{project_name_normalized}',
            }
        )
        if project_urls:
            for label, url in project_urls.items():
                if ' ' in label:
                    label = f'"{label}"'
                project_url_data += f'\n{label} = "{url.format(**template_config)}"'

        dependency_data = '['
        if template_config['dependencies']:
            for dependency in sorted(template_config['dependencies']):
                dependency_data += f'\n  "{dependency}",\n'
        dependency_data += ']'

        cli_scripts = ''
        if template_config['args']['cli']:
            cli_scripts = f"""

[project.scripts]
{template_config['project_name_normalized']} = "{template_config['package_name']}.cli:{template_config['package_name']}"\
"""  # noqa: E501

        tests_section = ''
        if plugin_config['tests']:
            package_location = 'src/' if plugin_config['src-layout'] else ''
            tests_section = f"""

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
python = ["3.7", "3.8", "3.9", "3.10", "3.11"]

[tool.hatch.envs.lint]
detached = true
dependencies = [
  "black>=23.1.0",
  "mypy>=1.0.0",
  "ruff>=0.0.243",
]
[tool.hatch.envs.lint.scripts]
typing = "mypy --install-types --non-interactive {{args:{package_location}{template_config['package_name']} tests}}"
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
select = [
  "A",
  "ARG",
  "B",
  "C",
  "DTZ",
  "E",
  "EM",
  "F",
  "FBT",
  "I",
  "ICN",
  "ISC",
  "N",
  "PLC",
  "PLE",
  "PLR",
  "PLW",
  "Q",
  "RUF",
  "S",
  "T",
  "TID",
  "UP",
  "W",
  "YTT",
]
ignore = [
  # Allow non-abstract empty methods in abstract base classes
  "B027",
  # Allow boolean positional values in function calls, like `dict.get(... True)`
  "FBT003",
  # Ignore checks for possible passwords
  "S105", "S106", "S107",
  # Ignore complexity
  "C901", "PLR0911", "PLR0912", "PLR0913", "PLR0915",
]
unfixable = [
  # Don't touch unused imports
  "F401",
]

[tool.ruff.isort]
known-first-party = ["{template_config['package_name']}"]

[tool.ruff.flake8-tidy-imports]
ban-relative-imports = "all"

[tool.ruff.per-file-ignores]
# Tests can use magic values, assertions, and relative imports
"tests/**/*" = ["PLR2004", "S101", "TID252"]

[tool.coverage.run]
source_pkgs = ["{template_config['package_name']}", "tests"]
branch = true
parallel = true
omit = [
  "{package_location}{template_config['package_name']}/__about__.py",
]

[tool.coverage.paths]
{template_config['package_name']} = ["{package_location}{template_config['package_name']}", "*/{template_config['project_name_normalized']}/{package_location}{template_config['package_name']}"]
tests = ["tests", "*/{template_config['project_name_normalized']}/tests"]

[tool.coverage.report]
exclude_lines = [
  "no cov",
  "if __name__ == .__main__.:",
  "if TYPE_CHECKING:",
]"""  # noqa: E501

        super().__init__(
            Path('pyproject.toml'),
            self.TEMPLATE.format(
                project_url_data=project_url_data,
                dependency_data=dependency_data,
                cli_scripts=cli_scripts,
                tests_section=tests_section,
                **template_config,
            ),
        )
