from hatch.structures import File

TEMPLATE = """\
language: python

matrix:
    include:{build_matrix}{pypy_install}

install:
  - pip install tox{coverage_package}

script: "tox -- -rs"{coverage_command}
"""


class TravisCI(File):
    def __init__(self, pyversions, coverage_service):
        build_matrix = ''
        pypy_versions = set()

        for version in pyversions:
            build_matrix += '\n        - python: {}'.format(version)
            build_matrix += '\n          env: TOXENV={}'.format(
                version if version.startswith('pypy') else ''.join(version.split('.'))
            )

            if version.startswith('pypy'):
                if version.startswith('pypy3'):
                    pypy_versions.add('pypy3')
                else:
                    pypy_versions.add('pypy')

        # Travis' PyPy is old
        pypy_install = ''
        if pypy_versions:
            pypy_install += '\n\n'
            pypy_install += 'before_install:\n'
            pypy_install += '  - cd $HOME\n'
            pypy_install += '  - mkdir bin\n'
            pypy_install += '  - export PATH=$HOME/bin:$PATH\n'

            if 'pypy' in pypy_versions:
                url = (
                    'https://bitbucket.org/squeaky/portable-pypy/downloads/pypy'
                    '-5.8-linux_x86_64-portable.tar.bz2'
                )
                archive = 'pypy-5.8-linux_x86_64-portable.tar.bz2'
                dirname = 'pypy-5.8-linux_x86_64-portable'
                pypy_install += (
                    "  - \"if [[ $TRAVIS_PYTHON_VERSION == 'pypy' ]]; then "
                    "deactivate && wget {url} && tar -jxvf {archive} && echo"
                    " 'Setting up aliases...' && cd {dirname}/bin/ && export"
                    " PATH=$PWD:$PATH && ln -s pypy python && echo 'Setting "
                    "up pip...' && ./pypy -m ensurepip ; fi\"\n".format(
                        url=url, archive=archive, dirname=dirname
                    )
                )

            if 'pypy3' in pypy_versions:
                url = (
                    'https://bitbucket.org/squeaky/portable-pypy/downloads/pypy'
                    '3.5-5.8-beta-linux_x86_64-portable.tar.bz2'
                )
                archive = 'pypy3.5-5.8-beta-linux_x86_64-portable.tar.bz2'
                dirname = 'pypy3.5-5.8-beta-linux_x86_64-portable'
                pypy_install += (
                    "  - \"if [[ $TRAVIS_PYTHON_VERSION == 'pypy3' ]]; then "
                    "deactivate && wget {url} && tar -jxvf {archive} && echo"
                    " 'Setting up aliases...' && cd {dirname}/bin/ && export"
                    " PATH=$PWD:$PATH && ln -s pypy3 python && echo 'Setting"
                    " up pip...' && ./pypy3 -m ensurepip && ln -s pip3 pip ;"
                    " fi\"\n".format(url=url, archive=archive, dirname=dirname)
                )

            pypy_install += '  - cd $TRAVIS_BUILD_DIR'

        if coverage_service is None:
            coverage_package = ''
            coverage_command = ''
        else:
            coverage_package = ' {}'.format(coverage_service.package)
            coverage_command = '\n\nafter_success:\n  - {}'.format(coverage_service.command)

        super(TravisCI, self).__init__(
            '.travis.yml',
            TEMPLATE.format(
                build_matrix=build_matrix, coverage_package=coverage_package,
                pypy_install=pypy_install,
                coverage_command=coverage_command
            )
        )
