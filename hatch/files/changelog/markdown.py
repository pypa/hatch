from pkg_resources import resource_string
from hatch.structures import File

class MarkdownChangelog(File):
    def __init__(self, package_url, version):
        TEMPLATE = resource_string("hatch", "templates/CHANGELOG.md").decode()

        super(MarkdownChangelog, self).__init__(
            'CHANGELOG.md',
            TEMPLATE.format(
                package_url=package_url,
                version=version
            )
        )
