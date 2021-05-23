import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from zipfile import ZipFile

import requests
import toml
from packaging.requirements import Requirement
from virtualenv import cli_run

try:
    from shutil import which
except ImportError:
    from distutils import spawn

    which = spawn.find_executable  # type: ignore

HERE = os.path.dirname(os.path.abspath(__file__))
ON_WINDOWS = platform.system() == 'Windows'


class EnvVars(dict):
    def __init__(self, env_vars=None, ignore=None):
        super(EnvVars, self).__init__(os.environ)
        self.old_env = dict(self)

        if env_vars is not None:
            self.update(env_vars)

        if ignore is not None:
            for env_var in ignore:
                self.pop(env_var, None)

    def __enter__(self):
        os.environ.clear()
        os.environ.update(self)

    def __exit__(self, exc_type, exc_value, traceback):
        os.environ.clear()
        os.environ.update(self.old_env)


def python_version_supported(project_config):
    requires_python = project_config['project'].get('requires-python', '')
    if requires_python:
        python_constraint = Requirement('requires_python{}'.format(requires_python)).specifier
        if not python_constraint.contains(str(sys.version_info[0])):
            return False

    return True


def download_file(url, file_name):
    response = requests.get(url, stream=True)
    with open(file_name, 'wb') as f:
        for chunk in response.iter_content(16384):
            f.write(chunk)


@contextmanager
def temp_dir():
    d = tempfile.mkdtemp()

    try:
        d = os.path.realpath(d)
        yield d
    finally:
        shutil.rmtree(d)


def main():
    backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), 'backend')
    with temp_dir() as links_dir:
        print('<<<<< Building backend >>>>>')
        subprocess.check_call([sys.executable, '-m', 'build', '--wheel', '-o', links_dir, backend_path])
        subprocess.check_call(
            [
                sys.executable,
                '-m',
                'pip',
                'download',
                '-q',
                '-d',
                links_dir,
                os.path.join(links_dir, os.listdir(links_dir)[0]),
            ]
        )

        for project in os.listdir(HERE):
            project_dir = os.path.join(HERE, project)
            if not os.path.isdir(project_dir):
                continue

            print('<<<<< Project: {} >>>>>'.format(project))
            project_config = {}
            potential_project_file = os.path.join(project_dir, 'pyproject.toml')

            # Not yet ported
            if os.path.isfile(potential_project_file):
                with open(potential_project_file, 'r') as f:
                    project_config.update(toml.loads(f.read()))

                if not python_version_supported(project_config):
                    print('--> Unsupported version of Python, skipping...')
                    continue

            with open(os.path.join(project_dir, 'data.json'), 'r') as f:
                test_data = json.loads(f.read())

            with temp_dir() as d:
                archive_name = '{}.zip'.format(project)
                archive_path = os.path.join(d, archive_name)

                print('--> Downloading archive...')
                download_file(test_data['archive_url'], archive_path)
                with ZipFile(archive_path) as zip_file:
                    zip_file.extractall(d)

                entries = os.listdir(d)
                entries.remove(archive_name)
                repo_dir = os.path.join(d, entries[0])

                project_file = os.path.join(repo_dir, 'pyproject.toml')
                if project_config:
                    shutil.copyfile(potential_project_file, project_file)
                else:
                    if not os.path.isfile(project_file):
                        sys.exit('--> Missing file: pyproject.toml')

                    with open(project_file, 'r') as f:
                        project_config.update(toml.loads(f.read()))

                    for requirement in project_config.get('build-system', {}).get('requires', []):
                        if Requirement(requirement).name == 'hatchling':
                            break
                    else:
                        sys.exit('--> Field `build-system.requires` must specify `hatchling` as a requirement')

                    if not python_version_supported(project_config):
                        print('--> Unsupported version of Python, skipping...')
                        continue

                for file_name in ('MANIFEST.in', 'setup.cfg', 'setup.py'):
                    possible_path = os.path.join(repo_dir, file_name)
                    if os.path.isfile(possible_path):
                        os.remove(possible_path)

                venv_dir = os.path.join(d, '.venv')
                print('--> Creating virtual environment...')
                cli_run([venv_dir, '--no-download', '--no-periodic-update', '--pip', 'embed'])

                exe_dir = os.path.join(venv_dir, 'Scripts' if ON_WINDOWS else 'bin')
                with EnvVars(
                    {'VIRTUAL_ENV': venv_dir, 'PATH': '{}{}{}'.format(exe_dir, os.pathsep, os.environ['PATH'])},
                    ignore=('__PYVENV_LAUNCHER__', 'PYTHONHOME'),
                ):
                    print('--> Installing project...')
                    subprocess.check_call(
                        [which('pip'), 'install', '-q', '--find-links', links_dir, '--no-index', '--no-deps', repo_dir]
                    )
                    print('--> Installing dependencies...')
                    subprocess.check_call([which('pip'), 'install', '-q', repo_dir])

                    print('--> Testing package...')
                    for statement in test_data['statements']:
                        subprocess.check_call([which('python'), '-c', statement])

                    scripts = project_config['project'].get('scripts', {})
                    if scripts:
                        print('--> Testing scripts...')
                        for script in scripts:
                            if not which(script):
                                sys.exit('--> Could not locate script: {}'.format(script))

                    print('--> Success!')


if __name__ == '__main__':
    main()
