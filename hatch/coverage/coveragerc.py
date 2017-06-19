from hatch.structures import File

TEMPLATE = """\
[run]
source =
    {package_name}
    tests
branch = True
omit =
    {package_name}/cli.py

[report]
exclude_lines =
    no qa
    no cov
    pragma: no cover
    if __name__ == .__main__.:
"""


class CoverageConfig(File):
    def __init__(self, package_name):
        super(CoverageConfig, self).__init__(
            '.coveragerc',
            TEMPLATE.format(package_name=package_name)
        )
