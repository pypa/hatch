from hatch.template import File
from hatch.utils.fs import Path


class PackageRoot(File):
    def __init__(self, template_config: dict, plugin_config: dict):
        super().__init__(Path(template_config['package_name'], '__init__.py'), '')


class MetadataFile(File):
    def __init__(self, template_config: dict, plugin_config: dict):
        super().__init__(Path(template_config['package_name'], '__about__.py'), "__version__ = '0.0.1'\n")


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
"""  # noqa: E501

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
dynamic = ["version"]

[project.urls]{project_url_data}{cli_scripts}

[tool.hatch.version]
path = "{package_metadata_file_path}"{tests_section}
"""

    def __init__(self, template_config: dict, plugin_config: dict):
        template_config = dict(template_config)
        template_config['name'] = repr(template_config['name'])[1:-1]

        project_url_data = ''
        if 'project_urls' in plugin_config:
            project_urls = plugin_config['project_urls']
        else:
            project_urls = {
                'Documentation': 'https://github.com/unknown/{project_name_normalized}#readme',
                'Issues': 'https://github.com/unknown/{project_name_normalized}/issues',
                'Source': 'https://github.com/unknown/{project_name_normalized}',
            }
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
  "pytest",
  "pytest-cov",
]
[tool.hatch.envs.default.scripts]
cov = "pytest --cov-report=term-missing --cov-config=pyproject.toml --cov={package_location}{template_config['package_name']} --cov=tests {{args}}"
no-cov = "cov --no-cov {{args}}"

[[tool.hatch.envs.test.matrix]]
python = ["37", "38", "39", "310", "311"]

[tool.coverage.run]
branch = true
parallel = true
omit = [
  "{package_location}{template_config['package_name']}/__about__.py",
]

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
