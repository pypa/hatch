import os
import shutil

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.env import install_packages
from hatch.utils import temp_chdir
from hatch.venv import create_venv, venv
from ..utils import read_file


def test_invalid_part():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])

        result = runner.invoke(hatch, ['grow', 'big'])
        init_file = os.path.join(d, 'ok', '__init__.py')
        contents = read_file(init_file)

        assert result.exit_code == 2
        assert contents == "__version__ = '0.0.1'\n"
        assert 'invalid choice' in result.output


def test_package_cwd():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])

        result = runner.invoke(hatch, ['grow', 'minor'])
        init_file = os.path.join(d, 'ok', '__init__.py')
        contents = read_file(init_file)

        assert result.exit_code == 0
        assert contents == "__version__ = '0.1.0'\n"
        assert 'Updated {}'.format(init_file) in result.output
        assert '0.0.1 -> 0.1.0' in result.output


def test_package_cwd_about():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])

        init_file = os.path.join(d, 'ok', '__init__.py')
        about_file = os.path.join(d, 'ok', '__about__.py')
        shutil.copyfile(init_file, about_file)

        result = runner.invoke(hatch, ['grow', 'minor'])

        assert result.exit_code == 0
        assert read_file(init_file) == "__version__ = '0.0.1'\n"
        assert read_file(about_file) == "__version__ = '0.1.0'\n"
        assert 'Updated {}'.format(about_file) in result.output
        assert '0.0.1 -> 0.1.0' in result.output


def test_init_cwd():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        os.chdir(os.path.join(d, 'ok'))

        result = runner.invoke(hatch, ['grow', 'patch'])
        init_file = os.path.join(d, 'ok', '__init__.py')
        contents = read_file(init_file)

        assert result.exit_code == 0
        assert contents == "__version__ = '0.0.2'\n"
        assert 'Updated {}'.format(init_file) in result.output
        assert '0.0.1 -> 0.0.2' in result.output


def test_package():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['egg', 'ok', '--basic'])

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            os.chdir(os.path.join(d, 'ok'))
            install_packages(['-e', '.'])
            os.chdir(d)

            result = runner.invoke(hatch, ['grow', 'fix', 'ok'])
            init_file = os.path.join(d, 'ok', 'ok', '__init__.py')
            contents = read_file(init_file)

        assert result.exit_code == 0
        assert contents == "__version__ = '0.0.2'\n"
        assert 'Updated {}'.format(init_file) in result.output
        assert '0.0.1 -> 0.0.2' in result.output


def test_package_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            result = runner.invoke(hatch, ['grow', 'fix', 'ok'])

        assert result.exit_code == 1
        assert '`{}` is not an editable package.'.format('ok') in result.output


def test_path_relative():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['egg', 'ok', '--basic'])

        result = runner.invoke(hatch, ['grow', 'major', '-p', 'ok'])
        init_file = os.path.join(d, 'ok', 'ok', '__init__.py')
        contents = read_file(init_file)

        assert result.exit_code == 0
        assert contents == "__version__ = '1.0.0'\n"
        assert 'Updated {}'.format(init_file) in result.output
        assert '0.0.1 -> 1.0.0' in result.output


def test_path_full():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['egg', 'ok', '--basic'])
        runner.invoke(hatch, ['egg', 'ko', '--basic'])
        os.chdir(os.path.join(d, 'ko'))

        result = runner.invoke(
            hatch,
            ['grow', 'fix', '-p', os.path.join(d, 'ok')]
        )
        init_file = os.path.join(d, 'ok', 'ok', '__init__.py')
        contents = read_file(init_file)

        assert result.exit_code == 0
        assert contents == "__version__ = '0.0.2'\n"
        assert 'Updated {}'.format(init_file) in result.output
        assert '0.0.1 -> 0.0.2' in result.output


def test_path_full_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['egg', 'ok', '--basic'])

        full_path = os.path.join(d, 'ko')
        result = runner.invoke(hatch, ['grow', 'fix', '-p', full_path])
        init_file = os.path.join(d, 'ok', 'ok', '__init__.py')
        contents = read_file(init_file)

        assert result.exit_code == 1
        assert contents == "__version__ = '0.0.1'\n"
        assert 'Directory `{}` does not exist.'.format(full_path) in result.output


def test_no_init():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['egg', 'ok', '--basic'])

        result = runner.invoke(hatch, ['grow', 'fix'])
        init_file = os.path.join(d, 'ok', 'ok', '__init__.py')
        contents = read_file(init_file)

        assert result.exit_code == 1
        assert contents == "__version__ = '0.0.1'\n"
        assert 'No init files found.' in result.output


def test_no_version():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        os.remove(os.path.join(d, 'ok', '__init__.py'))

        result = runner.invoke(hatch, ['grow', 'fix'])

        assert result.exit_code == 1
        assert 'Found init files:' in result.output
        assert os.path.join(d, 'tests', '__init__.py') in result.output
        assert 'Unable to find a version specifier.' in result.output


def test_multi_line_init():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        with open(os.path.join(d, 'ok', '__init__.py'), 'w') as f:
            f.write('__version__ = "123"\nok\n')

        result = runner.invoke(hatch, ['grow', 'fix'])

        assert result.exit_code == 1
        assert 'Unable to find a version specifier.' in result.output


def test_no_match():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic'])
        with open(os.path.join(d, 'ok', '__init__.py'), 'w') as f:
            f.write('__version__ = "123"')

        result = runner.invoke(hatch, ['grow', 'fix'])

        assert result.exit_code == 1
        assert 'Unable to find a version specifier.' in result.output
