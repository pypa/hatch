import os

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.env import install_packages
from hatch.utils import temp_chdir
from hatch.venv import create_venv, venv


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
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        create_test_passing(d)

        result = runner.invoke(hatch, ['test'])

        assert result.exit_code == 0
        assert '1 passed' in result.output


def test_failing_cwd():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        create_test_failing(d)

        result = runner.invoke(hatch, ['test'])

        assert result.exit_code == 1
        assert '1 failed' in result.output


def test_package():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic'])
        package_dir = os.path.join(d, 'ok')
        create_test_passing(package_dir)

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            os.chdir(package_dir)
            install_packages(['-e', '.'])
            os.chdir(d)

            result = runner.invoke(hatch, ['test', 'ok', '-g'])

        assert result.exit_code == 0
        assert '1 passed' in result.output


def test_package_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            result = runner.invoke(hatch, ['test', 'ok'])

        assert result.exit_code == 1
        assert '`{}` is not an editable package.'.format('ok') in result.output


def test_local():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic'])
        package_dir = os.path.join(d, 'ok')
        create_test_passing(package_dir)

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            install_packages(['-e', package_dir])
            result = runner.invoke(hatch, ['test', '-l', '-g'])

        assert result.exit_code == 0
        assert 'Package `ok` has been selected.' in result.output
        assert '1 passed' in result.output


def test_local_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            result = runner.invoke(hatch, ['test', '-l', '-g'])

        assert result.exit_code == 1
        assert 'There are no local packages available.' in result.output


def test_local_multiple():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic'])
        runner.invoke(hatch, ['new', 'ko', '--basic'])

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            install_packages(['-e', os.path.join(d, 'ok')])
            install_packages(['-e', os.path.join(d, 'ko')])

            result = runner.invoke(hatch, ['test', '-l', '-g'])

        assert result.exit_code == 1
        assert (
            'There are multiple local packages available. '
            'Select one with the optional argument.'
        ) in result.output


def test_path_relative():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic'])
        create_test_passing(os.path.join(d, 'ok'))

        result = runner.invoke(hatch, ['test', '-p', 'ok'])

        assert result.exit_code == 0
        assert '1 passed' in result.output


def test_path_full():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic'])
        runner.invoke(hatch, ['new', 'ko', '--basic'])
        package_dir = os.path.join(d, 'ok')
        create_test_passing(package_dir)

        os.chdir(os.path.join(d, 'ko'))
        result = runner.invoke(hatch, ['test', '-p', os.path.join(d, 'ok')])

        assert result.exit_code == 0
        assert '1 passed' in result.output


def test_path_full_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic'])

        full_path = os.path.join(d, 'ko')
        result = runner.invoke(hatch, ['test', '-p', full_path])

        assert result.exit_code == 1
        assert 'Directory `{}` does not exist.'.format(full_path) in result.output


def test_coverage_complete():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        create_test_complete_coverage(d, 'ok')

        result = runner.invoke(hatch, ['test', '-c'])

        assert result.exit_code == 0
        assert '1 passed' in result.output
        assert result.output.strip().endswith(' 100%')


def test_coverage_complete_merge():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        create_test_complete_coverage(d, 'ok')

        runner.invoke(hatch, ['test', '-c'])
        result = runner.invoke(hatch, ['test', '-c', '-m'])

        assert result.exit_code == 0
        assert '1 passed' in result.output
        assert result.output.strip().endswith(' 100%')


def test_coverage_incomplete():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        create_test_incomplete_coverage(d, 'ok')

        result = runner.invoke(hatch, ['test', '-c'])

        assert result.exit_code == 0
        assert '1 passed' in result.output
        assert not result.output.strip().endswith(' 100%')


def test_test_args():
    with temp_chdir():
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])

        result = runner.invoke(hatch, ['test', '-ta', '--help'])

        assert '-k EXPRESSION' in result.output


def test_coverage_args():
    with temp_chdir():
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])

        result = runner.invoke(hatch, ['test', '-c', '-ca', '--help'])

        assert '--parallel-mode' in result.output
