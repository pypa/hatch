import os

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.env import (
    get_installed_packages, get_package_version, install_packages
)
from hatch.utils import temp_chdir
from hatch.venv import create_venv, venv


def test_get_package_version_not_installed():
    assert get_package_version('the_knights_who_say_ni') == ''


def test_get_installed_packages_no_editable():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            install_packages(['six'])
            install_packages(['-e', '.'])
            assert get_installed_packages(editable=False) == ['pip', 'setuptools', 'six', 'wheel']
