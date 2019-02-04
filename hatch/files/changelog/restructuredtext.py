from pkg_resources import resource_string
from hatch.structures import File

class ReStructuredTextChangelog(File):
    def __init__(self, package_url, version):
        TEMPLATE = resource_string("hatch", "templates/CHANGELOG.rst").decode()

        super(ReStructuredTextChangelog, self).__init__(
            'CHANGELOG.rst',
            TEMPLATE.format(
                package_url=package_url,
                version=version
            )
        )
