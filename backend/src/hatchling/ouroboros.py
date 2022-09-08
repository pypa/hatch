import os

CONFIG = {
    'project': {
        'name': 'hatchling',
        'description': 'Modern, extensible Python build backend',
        'readme': 'README.md',
        'requires-python': '>=3.7',
        'license': 'MIT',
        'authors': [{'name': 'Ofek Lev', 'email': 'oss@ofek.dev'}],
        'urls': {
            'Homepage': 'https://hatch.pypa.io/latest/',
            'Sponsor': 'https://github.com/sponsors/ofek',
            'History': 'https://hatch.pypa.io/dev/history/',
            'Tracker': 'https://github.com/pypa/hatch/issues',
            'Source': 'https://github.com/pypa/hatch/tree/master/backend',
        },
        'keywords': ['build', 'hatch', 'packaging'],
        'classifiers': [
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Natural Language :: English',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.11',
            'Programming Language :: Python :: Implementation :: CPython',
            'Programming Language :: Python :: Implementation :: PyPy',
            'Topic :: Software Development :: Build Tools',
            'Topic :: Software Development :: Libraries :: Python Modules',
        ],
        'dependencies': [
            'editables>=0.3',
            'importlib-metadata; python_version < "3.8"',
            'packaging>=21.3',
            'pathspec>=0.10.1',
            'pluggy>=1.0.0',
            'tomli>=1.2.2; python_version < "3.11"',
        ],
        'scripts': {'hatchling': 'hatchling.cli:hatchling'},
        'dynamic': ['version'],
    },
    'tool': {
        'hatch': {
            'version': {'path': 'src/hatchling/__about__.py'},
        },
    },
}


def build_sdist(sdist_directory, config_settings=None):
    """
    https://peps.python.org/pep-0517/#build-sdist
    """
    from hatchling.builders.sdist import SdistBuilder

    builder = SdistBuilder(os.getcwd(), config=CONFIG)
    return os.path.basename(next(builder.build(sdist_directory, ['standard'])))


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    """
    https://peps.python.org/pep-0517/#build-wheel
    """
    from hatchling.builders.wheel import WheelBuilder

    builder = WheelBuilder(os.getcwd(), config=CONFIG)
    return os.path.basename(next(builder.build(wheel_directory, ['standard'])))


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    """
    https://peps.python.org/pep-0660/#build-editable
    """
    from hatchling.builders.wheel import WheelBuilder

    builder = WheelBuilder(os.getcwd(), config=CONFIG)
    return os.path.basename(next(builder.build(wheel_directory, ['editable'])))


def get_requires_for_build_sdist(config_settings=None):
    """
    https://peps.python.org/pep-0517/#get-requires-for-build-sdist
    """
    return CONFIG['project']['dependencies']


def get_requires_for_build_wheel(config_settings=None):
    """
    https://peps.python.org/pep-0517/#get-requires-for-build-wheel
    """
    return CONFIG['project']['dependencies']


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    """
    https://peps.python.org/pep-0517/#prepare-metadata-for-build-wheel
    """
    from hatchling.builders.wheel import WheelBuilder

    builder = WheelBuilder(os.getcwd(), config=CONFIG)

    directory = os.path.join(metadata_directory, f'{builder.artifact_project_id}.dist-info')
    if not os.path.isdir(directory):
        os.mkdir(directory)

    with open(os.path.join(directory, 'METADATA'), 'w', encoding='utf-8') as f:
        f.write(builder.config.core_metadata_constructor(builder.metadata))

    return os.path.basename(directory)


def get_requires_for_build_editable(config_settings=None):
    """
    https://peps.python.org/pep-0660/#get-requires-for-build-editable
    """
    return CONFIG['project']['dependencies']


def prepare_metadata_for_build_editable(metadata_directory, config_settings=None):
    """
    https://peps.python.org/pep-0660/#prepare-metadata-for-build-editable
    """
    from hatchling.builders.wheel import EDITABLES_MINIMUM_VERSION, WheelBuilder

    builder = WheelBuilder(os.getcwd(), config=CONFIG)

    directory = os.path.join(metadata_directory, f'{builder.artifact_project_id}.dist-info')
    if not os.path.isdir(directory):
        os.mkdir(directory)

    extra_dependencies = []
    if not builder.config.dev_mode_dirs and builder.config.dev_mode_exact:
        extra_dependencies.append(f'editables~={EDITABLES_MINIMUM_VERSION}')

    with open(os.path.join(directory, 'METADATA'), 'w', encoding='utf-8') as f:
        f.write(builder.config.core_metadata_constructor(builder.metadata, extra_dependencies=extra_dependencies))

    return os.path.basename(directory)
