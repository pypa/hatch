from hatch.io import File

BASE = """\
*.log
*.pyc
/.cache
/.coverage
/.idea
/{package_name}.egg-info
/build
/dist
/docs/build
/wheelhouse
"""


class GitIgnore(File):
    def __init__(self, package_name):
        super(GitIgnore, self).__init__(
            '.gitignore',
            BASE.format(package_name=package_name)
        )
