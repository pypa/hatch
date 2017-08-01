import os

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.env import install_packages
from hatch.utils import create_file, temp_chdir
from hatch.venv import create_venv, venv
from .utils import matching_file


def test_cwd():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])

        result = runner.invoke(hatch, ['build'])

        assert result.exit_code == 0
        assert matching_file(r'.*\.whl$', os.listdir(os.path.join(d, 'dist')))


def test_package():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['egg', 'ok', '--basic'])
        package_dir = os.path.join(d, 'ok')

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            os.chdir(package_dir)
            install_packages(['-e', '.'])
            os.chdir(d)

            result = runner.invoke(hatch, ['build', 'ok'])

        assert result.exit_code == 0
        assert matching_file(r'.*\.whl$', os.listdir(os.path.join(package_dir, 'dist')))


def test_package_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            result = runner.invoke(hatch, ['build', 'ok'])

        assert result.exit_code == 1
        assert '`{}` is not an editable package.'.format('ok') in result.output


def test_path_relative():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['egg', 'ok', '--basic'])

        result = runner.invoke(hatch, ['build', '-p', 'ok'])

        assert result.exit_code == 0
        assert matching_file(r'.*\.whl$', os.listdir(os.path.join(d, 'ok', 'dist')))


def test_path_full():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['egg', 'ok', '--basic'])
        runner.invoke(hatch, ['egg', 'ko', '--basic'])
        package_dir = os.path.join(d, 'ok')

        os.chdir(os.path.join(d, 'ko'))
        result = runner.invoke(hatch, ['build', '-p', package_dir])

        assert result.exit_code == 0
        assert matching_file(r'.*\.whl$', os.listdir(os.path.join(package_dir, 'dist')))


def test_path_full_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['egg', 'ok', '--basic'])

        full_path = os.path.join(d, 'ko')
        result = runner.invoke(hatch, ['build', '-p', full_path])

        assert result.exit_code == 1
        assert 'Directory `{}` does not exist.'.format(full_path) in result.output


def test_default_non_universal():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])

        result = runner.invoke(hatch, ['build'])
        file_name = os.listdir(os.path.join(d, 'dist'))[0]

        assert result.exit_code == 0
        assert 'py2' in file_name or 'py3' in file_name
        assert not ('py2' in file_name and 'py3' in file_name)


def test_universal():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])

        result = runner.invoke(hatch, ['build', '-u'])
        file_name = os.listdir(os.path.join(d, 'dist'))[0]

        assert result.exit_code == 0
        assert 'py2' in file_name and 'py3' in file_name


def test_platform_name():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])

        result = runner.invoke(hatch, ['build', '-n', 'linux_x86_64'])

        assert result.exit_code == 0
        assert matching_file(r'linux_x86_64\.whl$', os.listdir(os.path.join(d, 'dist')))


def test_build_dir():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])

        build_dir = os.path.join(d, '_build_dir')
        result = runner.invoke(hatch, ['build', '-d', build_dir])

        assert result.exit_code == 0
        assert matching_file(r'.*\.whl$', os.listdir(build_dir))


def test_clean():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])

        old_artifact = os.path.join(d, 'dist', 'foo.whl')
        create_file(old_artifact)
        assert os.path.exists(old_artifact)

        result = runner.invoke(hatch, ['build', '-c'])

        assert result.exit_code == 0
        assert matching_file(r'.*\.whl$', os.listdir(os.path.join(d, 'dist')))
        assert not os.path.exists(old_artifact)


def test_fail():
    with temp_chdir():
        runner = CliRunner()
        result = runner.invoke(hatch, ['build'])

        assert result.exit_code != 0
