from hatch.structures import File

TEMPLATE = """\
language: python

matrix:
    include:{build_matrix}

install:
  - pip install tox{coverage_package}
script: tox{coverage_command}"""


class TravisCI(File):
    def __init__(self, pyversions, coverage_service):
        build_matrix = ''

        for version in pyversions:
            if version.startswith('pypy'):
                tox_version = version
                if version.startswith('pypy3'):
                    pyversion = 'pypy3.5-5.8.0'
                else:
                    pyversion = 'pypy2.7-5.8.0'
            else:
                pyversion = version
                tox_version = 'py{}'.format(''.join(pyversion.split('.')))

            build_matrix += '\n        - python: {}'.format(pyversion)
            build_matrix += '\n          env: TOXENV={}'.format(tox_version)

        coverage_package = ''
        coverage_command = ''
        if coverage_service:
            coverage_package += ' {}'.format(coverage_service.package)
            coverage_command += '\n\nafter_success:\n  - {}'.format(coverage_service.command)

        # for `parse`
        coverage_package += '\n'
        coverage_command += '\n'

        super(TravisCI, self).__init__(
            '.travis.yml',
            TEMPLATE.format(
                build_matrix=build_matrix,
                coverage_package=coverage_package,
                coverage_command=coverage_command
            )
        )
