import os
import shutil

from click.testing import CliRunner

from hatch.cli import hatch
from hatch.env import install_packages
from hatch.settings import (
    SETTINGS_FILE, copy_default_settings, save_settings
)
from hatch.utils import basepath, temp_chdir, temp_move_path
from hatch.venv import create_venv, venv
from ..utils import read_file, wait_for_os


def test_invalid_part():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])

        result = runner.invoke(hatch, ['grow', 'big'])
        init_file = os.path.join(d, 'ok', '__init__.py')
        contents = read_file(init_file)

        assert result.exit_code == 2
        assert contents == "__version__ = '0.0.1'\n"
        assert 'invalid choice' in result.output


def test_package_cwd():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])

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
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])

        init_file = os.path.join(d, 'ok', '__init__.py')
        about_file = os.path.join(d, 'ok', '__about__.py')
        shutil.copyfile(init_file, about_file)

        result = runner.invoke(hatch, ['grow', 'minor'])

        assert result.exit_code == 0
        assert read_file(init_file) == "__version__ = '0.1.0'\n"
        assert 'Updated {}'.format(init_file) in result.output
        assert read_file(about_file) == "__version__ = '0.1.0'\n"
        assert 'Updated {}'.format(about_file) in result.output
        assert '0.0.1 -> 0.1.0' in result.output


def test_package_cwd_version():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])

        init_file = os.path.join(d, 'ok', '__init__.py')
        about_file = os.path.join(d, 'ok', '__about__.py')
        version_file = os.path.join(d, 'ok', '__version__.py')
        shutil.copyfile(init_file, about_file)
        shutil.copyfile(init_file, version_file)

        result = runner.invoke(hatch, ['grow', 'minor'])

        assert result.exit_code == 0
        assert read_file(init_file) == "__version__ = '0.1.0'\n"
        assert read_file(about_file) == "__version__ = '0.1.0'\n"
        assert read_file(version_file) == "__version__ = '0.1.0'\n"
        assert 'Updated {}'.format(version_file) in result.output
        assert '0.0.1 -> 0.1.0' in result.output


def test_package_path():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'zzz', '--basic', '-ne'])
        origin = os.path.join(d, 'zzz', 'zzz')

        package_dir = os.path.join(d, basepath(d))
        priority_dir = os.path.join(d, 'aaa')
        package_file = os.path.join(package_dir, '__init__.py')
        priority_file = os.path.join(priority_dir, '__init__.py')
        shutil.copytree(origin, package_dir)
        shutil.copytree(origin, priority_dir)

        result = runner.invoke(hatch, ['grow', 'minor'])
        wait_for_os()

        assert result.exit_code == 0
        assert read_file(priority_file) == "__version__ = '0.1.0'\n"
        assert read_file(package_file) == "__version__ = '0.1.0'\n"
        assert 'Updated {}'.format(package_file) in result.output
        assert '0.0.1 -> 0.1.0' in result.output


def test_src_package_path():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'zzz', '--basic', '-ne'])
        origin = os.path.join(d, 'zzz', 'zzz')

        project_name = basepath(d)
        src_package_dir = os.path.join(d, 'src', project_name)
        package_dir = os.path.join(d, project_name)
        priority_dir = os.path.join(d, 'aaa')
        src_package_file = os.path.join(src_package_dir, '__init__.py')
        package_file = os.path.join(package_dir, '__init__.py')
        priority_file = os.path.join(priority_dir, '__init__.py')
        shutil.copytree(origin, src_package_dir)
        shutil.copytree(origin, package_dir)
        shutil.copytree(origin, priority_dir)

        result = runner.invoke(hatch, ['grow', 'minor'])
        wait_for_os()

        assert result.exit_code == 0
        assert read_file(priority_file) == "__version__ = '0.1.0'\n"
        assert read_file(package_file) == "__version__ = '0.1.0'\n"
        assert read_file(src_package_file) == "__version__ = '0.1.0'\n"
        assert 'Updated {}'.format(src_package_file) in result.output
        assert '0.0.1 -> 0.1.0' in result.output


def test_init_cwd():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])
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
        runner.invoke(hatch, ['new', 'ok', '--basic', '-ne'])

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


def test_local():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic', '-ne'])

        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            install_packages(['-e', os.path.join(d, 'ok')])

            result = runner.invoke(hatch, ['grow', 'fix', '-l'])
            init_file = os.path.join(d, 'ok', 'ok', '__init__.py')
            contents = read_file(init_file)

        assert result.exit_code == 0
        assert contents == "__version__ = '0.0.2'\n"
        assert 'Package `ok` has been selected.' in result.output
        assert 'Updated {}'.format(init_file) in result.output
        assert '0.0.1 -> 0.0.2' in result.output


def test_local_not_exist():
    with temp_chdir() as d:
        runner = CliRunner()
        venv_dir = os.path.join(d, 'venv')
        create_venv(venv_dir)

        with venv(venv_dir):
            result = runner.invoke(hatch, ['grow', 'fix', '-l'])

        assert result.exit_code == 1
        assert 'There are no local packages available.' in result.output


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

            result = runner.invoke(hatch, ['grow', 'fix', '-l'])

        assert result.exit_code == 1
        assert (
            'There are multiple local packages available. '
            'Select one with the optional argument.'
        ) in result.output


def test_path_relative():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic', '-ne'])

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
        runner.invoke(hatch, ['new', 'ok', '--basic', '-ne'])
        runner.invoke(hatch, ['new', 'ko', '--basic', '-ne'])
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
        runner.invoke(hatch, ['new', 'ok', '--basic', '-ne'])

        full_path = os.path.join(d, 'ko')
        result = runner.invoke(hatch, ['grow', 'fix', '-p', full_path])
        init_file = os.path.join(d, 'ok', 'ok', '__init__.py')
        contents = read_file(init_file)

        assert result.exit_code == 1
        assert contents == "__version__ = '0.0.1'\n"
        assert 'Directory `{}` does not exist.'.format(full_path) in result.output


def test_path_file():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic', '-ne'])
        init_file = os.path.join(d, 'ok', 'ok', '__init__.py')

        result = runner.invoke(hatch, ['grow', 'major', '-p', init_file])
        contents = read_file(init_file)

        assert result.exit_code == 0
        assert contents == "__version__ = '1.0.0'\n"
        assert 'Updated {}'.format(init_file) in result.output
        assert '0.0.1 -> 1.0.0' in result.output


def test_no_init():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['new', 'ok', '--basic', '-ne'])

        result = runner.invoke(hatch, ['grow', 'fix'])
        init_file = os.path.join(d, 'ok', 'ok', '__init__.py')
        contents = read_file(init_file)

        assert result.exit_code == 1
        assert contents == "__version__ = '0.0.1'\n"
        assert 'No version files found.' in result.output


def test_no_version():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])
        os.remove(os.path.join(d, 'ok', '__init__.py'))

        result = runner.invoke(hatch, ['grow', 'fix'])

        assert result.exit_code == 1
        assert 'Found version files:' in result.output
        assert os.path.join(d, 'tests', '__init__.py') in result.output
        assert 'Unable to find a version specifier.' in result.output


def test_multi_line_init():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])
        with open(os.path.join(d, 'ok', '__init__.py'), 'w') as f:
            f.write('__version__ = "123"\nok\n')

        result = runner.invoke(hatch, ['grow', 'fix'])

        assert result.exit_code == 1
        assert 'Unable to find a version specifier.' in result.output


def test_no_match():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])
        with open(os.path.join(d, 'ok', '__init__.py'), 'w') as f:
            f.write('__version__ = "123"')

        result = runner.invoke(hatch, ['grow', 'fix'])

        assert result.exit_code == 1
        assert 'Unable to find a version specifier.' in result.output


def test_pre_config():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])
        init_file = os.path.join(d, 'ok', '__init__.py')

        with temp_move_path(SETTINGS_FILE, d):
            settings = copy_default_settings()
            settings['semver']['pre'] = 'dev'
            save_settings(settings)
            result = runner.invoke(hatch, ['grow', 'pre'])
            contents = read_file(init_file)

        assert result.exit_code == 0
        assert contents == "__version__ = '0.0.1-dev.1'\n"
        assert 'Updated {}'.format(init_file) in result.output
        assert '0.0.1 -> 0.0.1-dev.1' in result.output


def test_pre_option():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])
        init_file = os.path.join(d, 'ok', '__init__.py')

        with temp_move_path(SETTINGS_FILE, d):
            settings = copy_default_settings()
            settings['semver']['pre'] = 'rc'
            save_settings(settings)
            result = runner.invoke(hatch, ['grow', 'pre', '--pre', 'dev'])
            contents = read_file(init_file)

        assert result.exit_code == 0
        assert contents == "__version__ = '0.0.1-dev.1'\n"
        assert 'Updated {}'.format(init_file) in result.output
        assert '0.0.1 -> 0.0.1-dev.1' in result.output


def test_build_config():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])
        init_file = os.path.join(d, 'ok', '__init__.py')

        with temp_move_path(SETTINGS_FILE, d):
            settings = copy_default_settings()
            settings['semver']['build'] = 'nightly'
            save_settings(settings)
            result = runner.invoke(hatch, ['grow', 'build'])
            contents = read_file(init_file)

        assert result.exit_code == 0
        assert contents == "__version__ = '0.0.1+nightly.1'\n"
        assert 'Updated {}'.format(init_file) in result.output
        assert '0.0.1 -> 0.0.1+nightly.1' in result.output


def test_build_option():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])
        init_file = os.path.join(d, 'ok', '__init__.py')

        with temp_move_path(SETTINGS_FILE, d):
            settings = copy_default_settings()
            settings['semver']['build'] = 'rc'
            save_settings(settings)
            result = runner.invoke(hatch, ['grow', 'build', '--build', 'nightly'])
            contents = read_file(init_file)

        assert result.exit_code == 0
        assert contents == "__version__ = '0.0.1+nightly.1'\n"
        assert 'Updated {}'.format(init_file) in result.output
        assert '0.0.1 -> 0.0.1+nightly.1' in result.output


def test_no_config():
    with temp_chdir() as d:
        runner = CliRunner()
        runner.invoke(hatch, ['init', 'ok', '--basic', '-ne'])
        init_file = os.path.join(d, 'ok', '__init__.py')

        with temp_move_path(SETTINGS_FILE, d):
            result = runner.invoke(hatch, ['grow', 'pre'])
            contents = read_file(init_file)

        assert result.exit_code == 0
        assert contents == "__version__ = '0.0.1-rc.1'\n"
        assert 'Updated {}'.format(init_file) in result.output
        assert '0.0.1 -> 0.0.1-rc.1' in result.output
