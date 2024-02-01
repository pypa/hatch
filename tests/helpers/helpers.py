from __future__ import annotations

import importlib
import json
import os
import sys
from datetime import datetime, timezone
from functools import lru_cache
from textwrap import dedent as _dedent
from typing import TYPE_CHECKING

import tomli_w

from hatch.config.user import RootConfig
from hatch.env.utils import add_verbosity_flag
from hatch.python.core import InstalledDistribution
from hatch.python.resolve import get_distribution
from hatch.utils.toml import load_toml_file

if TYPE_CHECKING:
    from hatch.utils.fs import Path


def dedent(text):
    return _dedent(text[1:])


def remove_trailing_spaces(text):
    return ''.join(f'{line.rstrip()}\n' for line in text.splitlines(True))


def extract_requirements(lines):
    for raw_line in lines:
        line = raw_line.rstrip()
        if line and not line.startswith('#'):
            yield line


def get_current_timestamp():
    return datetime.now(timezone.utc).timestamp()


def assert_plugin_installation(subprocess_run, dependencies: list[str], *, verbosity=0):
    command = [
        sys.executable,
        '-u',
        '-m',
        'pip',
        'install',
        '--disable-pip-version-check',
        '--no-python-version-warning',
    ]
    add_verbosity_flag(command, verbosity, adjustment=-1)
    command.extend(dependencies)

    subprocess_run.assert_called_once_with(command, shell=False)


def assert_files(directory, expected_files, *, check_contents=True):
    start = str(directory)
    expected_relative_files = {str(f.path): f.contents for f in expected_files}
    seen_relative_file_paths = set()

    for root, _, files in os.walk(directory):
        relative_path = os.path.relpath(root, start)

        # First iteration
        if relative_path == '.':
            relative_path = ''

        for file_name in files:
            relative_file_path = os.path.join(relative_path, file_name)
            seen_relative_file_paths.add(relative_file_path)

            if check_contents and relative_file_path in expected_relative_files:
                with open(os.path.join(start, relative_file_path), encoding='utf-8') as f:
                    assert f.read() == expected_relative_files[relative_file_path], relative_file_path
            else:  # no cov
                pass

    expected_relative_file_paths = set(expected_relative_files)

    missing_files = expected_relative_file_paths - seen_relative_file_paths
    assert not missing_files, f'Missing files: {", ".join(sorted(missing_files))}'

    extra_files = seen_relative_file_paths - expected_relative_file_paths
    assert not extra_files, f'Extra files: {", ".join(sorted(extra_files))}'


def get_template_files(template_name, project_name, **kwargs):
    kwargs['project_name'] = project_name
    kwargs['project_name_normalized'] = project_name.lower().replace('.', '-')
    kwargs['package_name'] = kwargs['project_name_normalized'].replace('-', '_')

    config = RootConfig({})
    kwargs.setdefault('author', config.template.name)
    kwargs.setdefault('email', config.template.email)
    kwargs.setdefault('year', str(datetime.now(timezone.utc).year))

    return __load_template_module(template_name)(**kwargs)


@lru_cache
def __load_template_module(template_name):
    template = importlib.import_module(f'..templates.{template_name}', __name__)
    return template.get_files


def update_project_environment(project, name, config):
    project_file = project.root / 'pyproject.toml'
    raw_config = load_toml_file(str(project_file))

    env_config = raw_config.setdefault('tool', {}).setdefault('hatch', {}).setdefault('envs', {}).setdefault(name, {})
    env_config.update(config)

    project.config.envs[name] = project.config.envs.get(name, project.config.envs['default']).copy()
    project.config.envs[name].update(env_config)

    with open(str(project_file), 'w', encoding='utf-8') as f:
        f.write(tomli_w.dumps(raw_config))


def write_distribution(directory: Path, name: str):
    dist = get_distribution(name)
    path = directory / dist.name
    path.ensure_dir_exists()
    python_path = path / dist.python_path
    python_path.parent.ensure_dir_exists()
    python_path.touch()

    metadata = {'source': dist.source, 'python_path': dist.python_path}
    metadata_file = path / InstalledDistribution.metadata_filename()
    metadata_file.write_text(json.dumps(metadata))

    return InstalledDistribution(path, dist, metadata)


def downgrade_distribution_metadata(dist_dir: Path):
    metadata_file = dist_dir / InstalledDistribution.metadata_filename()
    metadata = json.loads(metadata_file.read_text())
    dist = InstalledDistribution(dist_dir, get_distribution(dist_dir.name), metadata)

    source = metadata['source']
    python_path = metadata['python_path']
    version = dist.version
    new_version = downgrade_version(version)
    new_source = source.replace(version, new_version)
    metadata['source'] = new_source

    # We also modify the Python path because some directory structures are determined
    # by the archive name which is itself determined by the source
    metadata['python_path'] = python_path.replace(version, new_version)
    if python_path != metadata['python_path']:
        new_python_path = dist_dir / metadata['python_path']
        new_python_path.parent.ensure_dir_exists()
        (dist_dir / python_path).rename(new_python_path)

    metadata_file.write_text(json.dumps(metadata))
    return metadata


def downgrade_version(version: str) -> str:
    major_version = version.split('.')[0]
    return version.replace(major_version, str(int(major_version) - 1), 1)
