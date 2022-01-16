import os

CONFIG = {
    'project': {
        'name': 'hatchling',
        'description': 'The build backend used by Hatch',
        'readme': 'README.md',
        'authors': [{'name': 'Ofek Lev', 'email': 'oss@ofek.dev'}],
        'urls': {
            'Documentation': 'https://ofek.dev/hatch/latest/',
            'Funding': 'https://github.com/sponsors/ofek',
            'History': 'https://ofek.dev/hatch/dev/meta/history/',
            'Issues': 'https://github.com/ofek/hatch/issues',
            'Source': 'https://github.com/ofek/hatch/tree/master/backend',
        },
        'license': 'MIT',
        'keywords': ['build', 'hatch', 'packaging'],
        'classifiers': [
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Natural Language :: English',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: Implementation :: CPython',
            'Programming Language :: Python :: Implementation :: PyPy',
            'Topic :: Software Development :: Build Tools',
            'Topic :: Software Development :: Libraries :: Python Modules',
        ],
        'dependencies': [
            'editables~=0.2; python_version > "3"',
            'importlib-metadata; python_version < "3.8"',
            'packaging~=21.3; python_version > "3"',
            'packaging~=20.9; python_version < "3"',
            'pathspec~=0.9',
            'pluggy~=1.0.0; python_version > "3"',
            'pluggy~=0.13; python_version < "3"',
            'toml~=0.10.2; python_version < "3"',
            'tomli~=2.0.0; python_version > "3"',
        ],
        'scripts': {'hatchling': 'hatchling.cli:hatchling'},
        'dynamic': ['version'],
    },
    'tool': {
        'hatch': {
            'version': {'path': 'hatchling/__about__.py'},
        },
    },
}


def build_sdist(sdist_directory, config_settings=None):
    """
    https://www.python.org/dev/peps/pep-0517/#build-sdist
    """
    from .builders.sdist import SdistBuilder

    builder = SdistBuilder(os.getcwd(), config=CONFIG)
    return os.path.basename(next(builder.build(sdist_directory, ['standard'])))


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    """
    https://www.python.org/dev/peps/pep-0517/#build-wheel
    """
    from .builders.wheel import WheelBuilder

    builder = WheelBuilder(os.getcwd(), config=CONFIG)
    return os.path.basename(next(builder.build(wheel_directory, ['standard'])))


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    """
    https://www.python.org/dev/peps/pep-0660/#build-editable
    """
    from .builders.wheel import WheelBuilder

    builder = WheelBuilder(os.getcwd(), config=CONFIG)
    return os.path.basename(next(builder.build(wheel_directory, ['editable'])))


def get_requires_for_build_sdist(config_settings=None):
    """
    https://www.python.org/dev/peps/pep-0517/#get-requires-for-build-sdist
    """
    return CONFIG['project']['dependencies']


def get_requires_for_build_wheel(config_settings=None):
    """
    https://www.python.org/dev/peps/pep-0517/#get-requires-for-build-wheel
    """
    return CONFIG['project']['dependencies']


def get_requires_for_build_editable(config_settings=None):
    """
    https://www.python.org/dev/peps/pep-0660/#get-requires-for-build-editable
    """
    return CONFIG['project']['dependencies']
