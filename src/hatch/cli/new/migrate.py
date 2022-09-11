import os
import sys

FILE = os.path.abspath(__file__)
HERE = os.path.dirname(FILE)
ENV_VAR_PREFIX = '_HATCHLING_PORT_ADD_'


def _apply_env_vars(kwargs):
    from ast import literal_eval

    for key, value in os.environ.items():
        if key.startswith(ENV_VAR_PREFIX):
            kwargs[key.replace(ENV_VAR_PREFIX, '', 1).lower()] = literal_eval(value)


def _parse_dependencies(dependency_definition):
    dependencies = []
    for line in dependency_definition.splitlines():
        line = line.split(' #', 1)[0].strip()
        if line:
            dependencies.append(line)

    return dependencies


def _collapse_data(output, data):
    import tomli_w

    expected_output = new_output = tomli_w.dumps(data)
    new_output = new_output.replace('    ', '')
    new_output = new_output.replace('[\n', '[')
    new_output = new_output.replace('",\n]', '"]')

    return output.replace(expected_output, new_output, 1)


def _parse_setup_cfg(kwargs):
    from configparser import ConfigParser

    setup_cfg_file = os.path.join(HERE, 'setup.cfg')
    if not os.path.isfile(setup_cfg_file):
        return

    setup_cfg = ConfigParser()
    setup_cfg.read(setup_cfg_file, encoding='utf-8')

    if not setup_cfg.has_section('metadata'):
        return

    metadata = setup_cfg['metadata']

    if 'name' in metadata and 'name' not in kwargs:
        kwargs['name'] = metadata['name']

    if 'description' in metadata and 'description' not in kwargs:
        kwargs['description'] = metadata['description']

    if 'license' in metadata and 'license' not in kwargs:
        kwargs['license'] = metadata['license']

    if 'author' in metadata and 'author' not in kwargs:
        kwargs['author'] = metadata['author']

    if 'author_email' in metadata and 'author_email' not in kwargs:
        kwargs['author_email'] = metadata['author_email']

    if 'keywords' in metadata and 'keywords' not in kwargs:
        keywords = metadata['keywords'].strip().splitlines()
        kwargs['keywords'] = keywords if len(keywords) > 1 else keywords[0]

    if 'classifiers' in metadata and 'classifiers' not in kwargs:
        kwargs['classifiers'] = metadata['classifiers'].strip().splitlines()

    if 'url' in metadata and 'url' not in kwargs:
        kwargs['url'] = metadata['url']

    if 'download_url' in metadata and 'download_url' not in kwargs:
        kwargs['download_url'] = metadata['download_url']

    if 'project_urls' in metadata and 'project_urls' not in kwargs:
        kwargs['project_urls'] = dict(
            url.replace(' = ', '=', 1).split('=') for url in metadata['project_urls'].strip().splitlines()
        )

    if setup_cfg.has_section('options'):
        options = setup_cfg['options']

        if 'python_requires' in options and 'python_requires' not in kwargs:
            kwargs['python_requires'] = options['python_requires']

        if 'install_requires' in options and 'install_requires' not in kwargs:
            kwargs['install_requires'] = _parse_dependencies(options['install_requires'])

        if 'packages' in options and 'packages' not in kwargs:
            packages = []
            for package in options['packages'].strip().splitlines():
                package = package.replace('find:', '', 1).replace('find_namespace:', '', 1).strip()
                if package:
                    packages.append(package)

            if packages:
                kwargs['packages'] = packages

        if 'package_dir' in options and 'package_dir' not in kwargs:
            kwargs['package_dir'] = dict(
                d.replace(' = ', '=', 1).split('=') for d in options['package_dir'].strip().splitlines()
            )

    if setup_cfg.has_section('options.extras_require') and 'extras_require' not in kwargs:
        kwargs['extras_require'] = {
            feature: _parse_dependencies(dependencies)
            for feature, dependencies in setup_cfg['options.extras_require'].items()
        }

    if setup_cfg.has_section('options.entry_points') and 'entry_points' not in kwargs:
        kwargs['entry_points'] = {
            entry_point: definitions.strip().splitlines()
            for entry_point, definitions in setup_cfg['options.entry_points'].items()
        }


def setup(**kwargs):
    import itertools
    import re

    import tomli_w

    project_metadata = {}
    hatch_metadata = {}
    tool_metadata = {'hatch': hatch_metadata}
    project_data = {
        'build-system': {'requires': ['hatchling'], 'build-backend': 'hatchling.build'},
        'project': project_metadata,
        'tool': tool_metadata,
    }

    _parse_setup_cfg(kwargs)
    _apply_env_vars(kwargs)

    name = kwargs['name']
    project_name = name.replace('_', '-')
    packages = sorted(kwargs.get('packages') or [name.replace('-', '_')])
    package_name = package_path = package_source = packages[0].split('.')[0].lower()

    project_metadata['name'] = project_name

    project_metadata['dynamic'] = ['version']

    if 'description' in kwargs:
        project_metadata['description'] = kwargs['description']

    for readme_file in ('README.md', 'README.rst', 'README.txt'):
        if os.path.isfile(os.path.join(HERE, readme_file)):
            project_metadata['readme'] = readme_file
            break

    project_metadata['license'] = kwargs.get('license', '')

    if 'python_requires' in kwargs:
        project_metadata['requires-python'] = kwargs['python_requires']

    for collaborator in ('author', 'maintainer'):
        collaborators = []
        collaborator_names = []
        collaborator_emails = []
        if collaborator in kwargs:
            for collaborator_name in kwargs[collaborator].split(','):
                collaborator_names.append(collaborator_name.strip())
        if f'{collaborator}_email' in kwargs:
            for collaborator_email in kwargs[f'{collaborator}_email'].split(','):
                collaborator_emails.append(collaborator_email.strip())

        for collaborator_name, collaborator_email in itertools.zip_longest(collaborator_names, collaborator_emails):
            data = {}
            if collaborator_name is not None:
                data['name'] = collaborator_name
            if collaborator_email is not None:
                data['email'] = collaborator_email
            if data:
                collaborators.append(data)

        if collaborators:
            project_metadata[f'{collaborator}s'] = collaborators

    if 'keywords' in kwargs:
        keywords = kwargs['keywords']
        if isinstance(keywords, str):
            keywords = keywords.replace(',', ' ').split()
        project_metadata['keywords'] = sorted(keywords)

    if 'classifiers' in kwargs:
        project_metadata['classifiers'] = sorted(kwargs['classifiers'])
        fixed_indices = []
        final_index = 0
        for i, classifier in enumerate(project_metadata['classifiers']):
            if classifier.startswith('Programming Language :: Python :: '):
                final_index = i
                for python_version in ('3.10', '3.11', '3.12'):
                    if classifier.endswith(python_version):
                        fixed_indices.append(i)
                        break
        for i, index in enumerate(fixed_indices):
            project_metadata['classifiers'].insert(final_index, project_metadata['classifiers'].pop(index - i))

    if 'install_requires' in kwargs:
        project_metadata['dependencies'] = sorted(
            [entry.strip() for entry in kwargs['install_requires']]
            if isinstance(kwargs['install_requires'], (list, tuple))
            else _parse_dependencies(kwargs['install_requires']),
            key=lambda d: d.lower(),
        )

    if 'extras_require' in kwargs:
        project_metadata['optional-dependencies'] = {
            group: sorted(
                [entry.strip() for entry in dependencies]
                if isinstance(dependencies, (list, tuple))
                else _parse_dependencies(dependencies),
                key=lambda d: d.lower(),
            )
            for group, dependencies in sorted(kwargs['extras_require'].items())
        }

    if 'entry_points' in kwargs and isinstance(kwargs['entry_points'], dict):
        entry_points = {}
        for entry_point, definitions in kwargs['entry_points'].items():
            if isinstance(definitions, str):
                definitions = [definitions]
            definitions = dict(sorted(d.replace(' ', '').split('=', 1) for d in definitions))

            if entry_point == 'console_scripts':
                project_metadata['scripts'] = definitions
            elif entry_point == 'gui_scripts':
                project_metadata['gui-scripts'] = definitions
            else:
                entry_points[entry_point] = definitions
        if entry_points:
            project_metadata['entry-points'] = dict(sorted(entry_points.items()))

    urls = {}
    if 'url' in kwargs:
        urls['Homepage'] = kwargs['url']
    if 'download_url' in kwargs:
        urls['Download'] = kwargs['download_url']
    if 'project_urls' in kwargs:
        urls.update(kwargs['project_urls'])
    if urls:
        project_metadata['urls'] = dict(sorted(urls.items()))

    build_targets = {}
    build_data = {}

    if 'use_scm_version' in kwargs:
        project_data['build-system']['requires'].append('hatch-vcs')
        hatch_metadata['version'] = {'source': 'vcs'}
        build_data['hooks'] = {'vcs': {'version-file': f'{package_path}/_version.py'}}
    else:
        hatch_metadata['version'] = {'path': f'{package_path}/__init__.py'}

    build_data['targets'] = build_targets

    if '' in kwargs.get('package_dir', {}):
        package_source = kwargs['package_dir']['']

        package = (kwargs.get('packages') or [package_name])[0]
        package_path = f'{package_source}/{package}'

        if package_path != f'src/{package_name}':
            build_targets.setdefault('wheel', {})['packages'] = [package_path]

    if kwargs.get('data_files', []):
        shared_data = {}
        for shared_directory, relative_paths in kwargs['data_files']:
            relative_files = {}
            for relative_path in relative_paths:
                relative_directory, filename = os.path.split(relative_path)
                relative_files.setdefault(relative_directory, []).append(filename)

            for relative_directory, files in sorted(relative_files.items()):
                if not os.path.isdir(relative_directory) or set(os.listdir(relative_directory)) != set(files):
                    for filename in sorted(files):
                        local_path = os.path.join(relative_directory, filename).replace('\\', '/')
                        shared_data[local_path] = f'{shared_directory}/{filename}'
                else:
                    shared_data[relative_directory] = shared_directory

        build_targets.setdefault('wheel', {})['shared-data'] = shared_data

    build_targets['sdist'] = {
        'include': [
            f'/{package_source}',
        ]
    }

    hatch_metadata['build'] = build_data

    output = tomli_w.dumps(project_data)
    output = _collapse_data(output, {'requires': project_data['build-system']['requires']})
    output = _collapse_data(output, {'dynamic': project_data['project']['dynamic']})

    project_file = os.path.join(HERE, 'pyproject.toml')
    if os.path.isfile(project_file):
        with open(project_file, encoding='utf-8') as f:
            current_contents = f.read()

        for section in ('build-system', 'project'):
            for pattern in (fr'^\[{section}].*?(?=^\[)', fr'^\[{section}].*'):
                current_contents = re.sub(pattern, '', current_contents, flags=re.MULTILINE | re.DOTALL)

        output += f'\n{current_contents}'

    with open(project_file, 'w', encoding='utf-8') as f:
        f.write(output)


if __name__ == 'setuptools':
    __this_shim = sys.modules.pop('setuptools')
    __current_directory = sys.path.pop(0)

    import setuptools as __real_setuptools

    sys.path.insert(0, __current_directory)
    sys.modules['setuptools'] = __this_shim

    def __getattr__(name):
        return getattr(__real_setuptools, name)

    del __this_shim
    del __current_directory


def migrate(root, setuptools_options):
    import shutil
    import subprocess
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as temp_dir:
        repo_dir = os.path.join(os.path.realpath(temp_dir), 'repo')
        shutil.copytree(root, repo_dir, ignore=shutil.ignore_patterns('.git', '.tox'), copy_function=shutil.copy)
        shutil.copy(FILE, os.path.join(repo_dir, 'setuptools.py'))
        os.chdir(repo_dir)

        try:
            env = dict(os.environ)
            for arg in setuptools_options:
                key, value = arg.split('=', 1)
                env[f'{ENV_VAR_PREFIX}{key}'] = value

            subprocess.check_call([sys.executable, os.path.join(repo_dir, 'setup.py')], env=env)

            old_project_file = os.path.join(root, 'pyproject.toml')
            new_project_file = os.path.join(repo_dir, 'pyproject.toml')
            shutil.copyfile(new_project_file, old_project_file)
        finally:
            os.chdir(root)
