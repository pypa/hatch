import os

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.env import (
    get_editable_packages, get_installed_packages, install_packages
)
from hatch.utils import env_vars, temp_chdir
from hatch.venv import create_venv, is_venv, venv
from ..utils import requires_internet, wait_until


def create_test_passing(d):
    with open(os.path.join(d, 'tests', 'test_add.py'), 'w') as f:
        f.write(
            'def test_add():\n'
            '    assert 1 + 2 == 3\n'
        )


def create_test_failing(d):
    with open(os.path.join(d, 'tests', 'test_add.py'), 'w') as f:
        f.write(
            'def test_add():\n'
            '    assert 1 + 2 != 3\n'
        )


def create_test_complete_coverage(d, pkg):
    with open(os.path.join(d, pkg, 'core.py'), 'w') as f:
        f.write(
            'def square_5():\n'
            '    return 5 ** 2\n'
        )
    with open(os.path.join(d, 'tests', 'test_core.py'), 'w') as f:
        f.write(
            'from {pkg}.core import square_5\n'
            'def test_square_5():\n'
            '    assert square_5() == 25\n'.format(pkg=pkg)
        )


def create_test_incomplete_coverage(d, pkg):
    with open(os.path.join(d, pkg, 'core.py'), 'w') as f:
        f.write(
            'def square_5():\n'
            '    return 5 ** 2\n'
        )
    with open(os.path.join(d, 'tests', 'test_add.py'), 'w') as f:
        f.write(
            'import {}\n'
            'def test_add():\n'
            '    assert 1 + 2 == 3\n'.format(pkg)
        )


def test_passing_cwd():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])
        create_test_passing(d)

        result = runner.invoke(hatch, ['test', '-nd'])

        assert result.exit_code == 0
        assert '1 passed' in result.output


def test_failing_cwd():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])
        create_test_failing(d)

        result = runner.invoke(hatch, ['test', '-nd'])

        assert result.exit_code == 1
        assert '1 failed' in result.output


@requires_internet
def test_project_existing_venv():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        venv_dir = os.path.join(d, 'venv')
        wait_until(is_venv, venv_dir)
        with venv(venv_dir):
            install_packages(['pytest', 'coverage'])
            installed_packages = get_installed_packages(editable=False)
            assert 'pytest' in installed_packages
            assert 'coverage' in installed_packages

        create_test_passing(d)
        with env_vars({'_IGNORE_VENV_': '1'}):
            result = runner.invoke(hatch, ['test'])

        assert result.exit_code == 0
        assert '1 passed' in result.output


@requires_internet
def test_project_no_venv():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])

        create_test_passing(d)
        with env_vars({'_IGNORE_VENV_': '1'}):
            result = runner.invoke(hatch, ['test'])

        with venv(os.path.join(d, 'venv')):
            assert 'ok' in get_editable_packages()
            installed_packages = get_installed_packages(editable=False)
            assert 'pytest' in installed_packages
            assert 'coverage' in installed_packages

        assert result.exit_code == 0
        assert 'A project has been detected!' in result.output
        assert 'Creating a dedicated virtual env... complete!' in result.output
        assert 'Installing this project in the virtual env...' in result.output
        assert 'Ensuring pytest and coverage are available...' in result.output
        assert '1 passed' in result.output


@requires_internet
def test_project_no_venv_install_dev_requirements():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])
        with open(os.path.join(d, 'dev-requirements.txt'), 'w') as f:
            f.write('six\n')

        create_test_passing(d)
        with env_vars({'_IGNORE_VENV_': '1'}):
            result = runner.invoke(hatch, ['test'])

        with venv(os.path.join(d, 'venv')):
            assert 'ok' in get_editable_packages()
            installed_packages = get_installed_packages(editable=False)
            assert 'pytest' in installed_packages
            assert 'coverage' in installed_packages
            assert 'six' in installed_packages

        assert result.exit_code == 0
        assert 'A project has been detected!' in result.output
        assert 'Creating a dedicated virtual env... complete!' in result.output
        assert 'Installing this project in the virtual env...' in result.output
        assert 'Ensuring pytest and coverage are available...' in result.output
        assert 'Installing test dependencies in the virtual env...' in result.output
        assert '1 passed' in result.output


@requires_internet
def test_project_no_venv_coverage():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])
        create_test_complete_coverage(d, 'ok')

        with env_vars({'_IGNORE_VENV_': '1'}):
            result = runner.invoke(hatch, ['test', '-c'])

        assert result.exit_code == 0
        assert '1 passed' in result.output
        assert result.output.strip().endswith(' 100%')


@requires_internet
def test_project_no_venv_coverage_merge():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])
        create_test_complete_coverage(d, 'ok')

        with env_vars({'_IGNORE_VENV_': '1'}):
            runner.invoke(hatch, ['test', '-c'])
            result = runner.invoke(hatch, ['test', '-c', '-m'])

        assert result.exit_code == 0
        assert '1 passed' in result.output
        assert result.output.strip().endswith(' 100%')


@requires_internet
def test_package():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic', '-ne'])
        package_dir = os.path.join(d, 'ok')
        create_test_passing(package_dir)

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            os.chdir(package_dir)
            install_packages(['-e', '.'])
            os.chdir(d)

            result = runner.invoke(hatch, ['test', '-nd', 'ok', '-g'])

        assert result.exit_code == 0
        assert '1 passed' in result.output


def test_package_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            result = runner.invoke(hatch, ['test', '-nd', 'ok'])

        assert result.exit_code == 1
        assert '`{}` is not an editable package.'.format('ok') in result.output


@requires_internet
def test_local():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic', '-ne'])
        package_dir = os.path.join(d, 'ok')
        create_test_passing(package_dir)

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            install_packages(['-e', package_dir])
            result = runner.invoke(hatch, ['test', '-nd', '-l', '-g'])

        assert result.exit_code == 0
        assert 'Package `ok` has been selected.' in result.output
        assert '1 passed' in result.output


def test_local_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            result = runner.invoke(hatch, ['test', '-nd', '-l', '-g'])

        assert result.exit_code == 1
        assert 'There are no local packages available.' in result.output


@requires_internet
def test_local_multiple():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic', '-ne'])
        runner.invoke(hatch, ['new', 'ko', '--basic', '-ne'])

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            install_packages(['-e', os.path.join(d, 'ok')])
            install_packages(['-e', os.path.join(d, 'ko')])

            result = runner.invoke(hatch, ['test', '-nd', '-l', '-g'])

        assert result.exit_code == 1
        assert (
            'There are multiple local packages available. '
            'Select one with the optional argument.'
        ) in result.output


def test_path_relative():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic', '-ne'])
        create_test_passing(os.path.join(d, 'ok'))

        result = runner.invoke(hatch, ['test', '-nd', '-p', 'ok'])

        assert result.exit_code == 0
        assert '1 passed' in result.output


def test_path_full():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic', '-ne'])
        runner.invoke(hatch, ['new', 'ko', '--basic', '-ne'])
        package_dir = os.path.join(d, 'ok')
        create_test_passing(package_dir)

        os.chdir(os.path.join(d, 'ko'))
        result = runner.invoke(hatch, ['test', '-nd', '-p', os.path.join(d, 'ok')])

        assert result.exit_code == 0
        assert '1 passed' in result.output


def test_path_full_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic', '-ne'])

        full_path = os.path.join(d, 'ko')
        result = runner.invoke(hatch, ['test', '-nd', '-p', full_path])

        assert result.exit_code == 1
        assert 'Directory `{}` does not exist.'.format(full_path) in result.output


def test_coverage_complete():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])
        create_test_complete_coverage(d, 'ok')

        result = runner.invoke(hatch, ['test', '-nd', '-c'])

        assert result.exit_code == 0
        assert '1 passed' in result.output
        assert result.output.strip().endswith(' 100%')


def test_coverage_complete_merge():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])
        create_test_complete_coverage(d, 'ok')

        runner.invoke(hatch, ['test', '-nd', '-c'])
        result = runner.invoke(hatch, ['test', '-nd', '-c', '-m'])

        assert result.exit_code == 0
        assert '1 passed' in result.output
        assert result.output.strip().endswith(' 100%')


def test_coverage_incomplete():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])
        create_test_incomplete_coverage(d, 'ok')

        result = runner.invoke(hatch, ['test', '-nd', '-c'])

        assert result.exit_code == 0
        assert '1 passed' in result.output
        assert not result.output.strip().endswith(' 100%')


def test_test_args():
    with temp_chdir():
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])

        result = runner.invoke(hatch, ['test', '-nd', '-ta', '--help'])

        assert '-k EXPRESSION' in result.output


def test_coverage_args():
    with temp_chdir():
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])

        result = runner.invoke(hatch, ['test', '-nd', '-c', '-ca', '--help'])

        assert '--parallel-mode' in result.output
