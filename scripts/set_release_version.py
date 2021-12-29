import os

from packaging.version import Version

from hatch.project.core import Project
from hatch.utils.fs import Path


def main():
    project = Project(Path(__file__).resolve().parent.parent)
    version = Version(project.metadata.version)
    with open(os.environ['GITHUB_ENV'], 'a', encoding='utf-8') as f:
        f.write(f'HATCH_DOCS_VERSION={version.major}.{version.minor}\n')


if __name__ == '__main__':
    main()
