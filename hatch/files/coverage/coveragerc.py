from hatch.structures import File
from hatch.utils import normalize_package_name

TEMPLATE = """\
[run]
source =
    {package_name_normalized}
    tests
branch = True
omit =
    {package_name_normalized}/cli.py

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
            TEMPLATE.format(package_name_normalized=normalize_package_name(package_name))
        )
