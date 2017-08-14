from hatch.structures import File
from hatch.utils import normalize_package_name

TEMPLATE = """\
[run]
source =
    {package_name_normalized}
    tests
branch = True
omit =
    {package_name_normalized}/{cli_file}.py

[report]
exclude_lines =
    no cov
    no qa
    noqa
    pragma: no cover
    if __name__ == .__main__.:
"""


class CoverageConfig(File):
    def __init__(self, package_name, cli):
        super(CoverageConfig, self).__init__(
            '.coveragerc',
            TEMPLATE.format(
                package_name_normalized=normalize_package_name(package_name),
                cli_file='__main__' if cli else 'cli'
            )
        )
