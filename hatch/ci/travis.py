from hatch.structures import File

BASE = """\
language: python

matrix:
    include:{build_matrix}

install:
  - pip install tox{coverage_package}

script: "tox -- -rs"{coverage_command}
"""


class TravisCI(File):
    def __init__(self, pyversions, coverage_service):
        build_matrix = ''

        for version in pyversions:
            build_matrix += '\n        - python: {}'.format(version)
            build_matrix += '\n          env: TOXENV={}'.format(
                version if version.startswith('pypy') else ''.join(version.split('.'))
            )

        if coverage_service is None:
            coverage_package = ''
            coverage_command = ''
        else:
            coverage_package = ' {}'.format(coverage_service.package)
            coverage_command = '\n\nafter_success:\n  - {}'.format(coverage_service.command)

        super(TravisCI, self).__init__(
            '.travis.yml',
            BASE.format(
                build_matrix=build_matrix, coverage_package=coverage_package,
                coverage_command=coverage_command
            )
        )
