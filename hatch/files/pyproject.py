from hatch.structures import File

TEMPLATE = """\
[metadata]
name = '{name}'
version = '{version}'
description = '{description}'
author = '{author}'
author_email = '{author_email}'
license = '{license}'
url = '{url}'

[requires]
python_version = {python_version}

[build-system]
requires = ['setuptools', 'wheel']

[tool.hatch.commands]
prerelease = 'hatch build'
"""


class ProjectFile(File):
    def __init__(self, name, version, author, email, description, pyversions, licenses, package_url):
        super(ProjectFile, self).__init__(
            'pyproject.toml',
            TEMPLATE.format(
                name=name,
                version=version,
                author=author,
                author_email=email,
                description=description,
                url=package_url,
                license='/'.join(li.short_name for li in licenses),
                python_version=pyversions,
            )
        )
