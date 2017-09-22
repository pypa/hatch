from hatch.structures import File
from hatch.utils import normalize_package_name

TEMPLATE = """\
*.log
*.pyc
.cache/
.coverage
.idea/
.vscode/
{package_name_normalized}.egg-info/
build/
dist/
docs/build/
venv/
wheelhouse/
"""


class GitIgnore(File):
    def __init__(self, package_name):
        super(GitIgnore, self).__init__(
            '.gitignore',
            TEMPLATE.format(package_name_normalized=normalize_package_name(package_name))
        )
