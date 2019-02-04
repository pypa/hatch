from pkg_resources import resource_string
from hatch.structures import File
from hatch.utils import normalize_package_name

class GitIgnore(File):
    def __init__(self, package_name):
        TEMPLATE = resource_string("hatch", "templates/dot.gitignore").decode()
        super(GitIgnore, self).__init__(
            '.gitignore',
            TEMPLATE.format(package_name_normalized=normalize_package_name(package_name))
        )
