from hatch.structures import File

TEMPLATE = """\
[[source]]
name = '{name}'
version = '{version}'
description = '{description}'
author = '{author}'
author_email = '{author_email}'
license = '{license}'
url = '{url}'

[requires]
python_version = {python_version}


[dev-packages]
pytest = '3.2.2'

[packages]
# requests = '2.18'


[commands]
prerelease = 'hatch build'
"""


class ProjectFile(File):
    def __init__(self, name, version, author, email, pyversions, licenses,
            package_url):
        super(ProjectFile, self).__init__(
            'pyproject.toml',
            TEMPLATE.format(
                name=name,
                version=version,
                author_email=email,
                author=author,
                description='',
                url=package_url,
                license='/'.join(li.short_name for li in licenses),
                python_version=pyversions,
            )
        )
