from hatch.structures import File

TEMPLATE = """\
[tox]
envlist ={build_matrix}

[testenv]
passenv = *
deps =
    coverage
    pytest{coverage_package}commands =
    python setup.py --quiet clean develop
    coverage run --parallel-mode -m pytest
    coverage combine --append
    coverage report -m
"""


class Tox(File):
    def __init__(self, pyversions, coverage_service):
        build_matrix = ''

        for version in pyversions:
            build_matrix += '\n    {},'.format(
                version if version.startswith('pypy')
                else 'py{}'.format(''.join(version.split('.')))
            )

        coverage_package = ''
        if coverage_service:
            coverage_package += '\n    {}'.format(coverage_service.package)

        coverage_package += '\n'

        super(Tox, self).__init__(
            'tox.ini',
            TEMPLATE.format(
                build_matrix=build_matrix, coverage_package=coverage_package
            )
        )
