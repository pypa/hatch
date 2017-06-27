import os

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.utils import install_packages
from hatch.venv import create_venv, venv
from .utils import get_version_as_bytes, temp_chdir


def test_requirements():
    with temp_chdir() as d:
        with open(os.path.join(d, 'requirements.txt'), 'w') as f:
            f.write('requests==2.18.1\n')

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            install_packages(['requests==2.17.3'])
            initial_version = get_version_as_bytes()
            runner = CliRunner()
            result = runner.invoke(hatch, ['update'])
            final_version = get_version_as_bytes()

        assert result.exit_code == 0
        assert initial_version < final_version


def test_requirements_none():
    with temp_chdir() as d:
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            runner = CliRunner()
            result = runner.invoke(hatch, ['update'])

        assert result.exit_code == 1
        assert 'Unable to locate a requirements file.' in result.output


def test_all_packages():
    with temp_chdir() as d:
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            install_packages(['requests==2.17.3'])
            initial_version = get_version_as_bytes()
            runner = CliRunner()
            result = runner.invoke(hatch, ['update', '--all'])
            final_version = get_version_as_bytes()

        assert result.exit_code == 0
        assert initial_version < final_version


def test_all_packages_none():
    with temp_chdir() as d:
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            runner = CliRunner()
            result = runner.invoke(hatch, ['update', '--all'])

        assert result.exit_code == 1
        assert 'No packages installed.' in result.output
