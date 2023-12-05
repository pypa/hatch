import json
import secrets

import pytest

from hatch.python.core import InstalledDistribution
from hatch.python.distributions import ORDERED_DISTRIBUTIONS
from hatch.python.resolve import get_distribution
from hatch.utils.structures import EnvVars


def test_unknown(hatch, helpers, path_append, mocker):
    install = mocker.patch('hatch.python.core.PythonManager.install')

    result = hatch('python', 'install', 'foo', 'bar')

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Unknown distributions: foo, bar
        """
    )

    install.assert_not_called()
    path_append.assert_not_called()


def test_incompatible_single(hatch, helpers, path_append, platform, dist_name, mocker):
    install = mocker.patch('hatch.python.core.PythonManager.install')

    with EnvVars({f'HATCH_PYTHON_VARIANT_{platform.name.upper()}': 'foo'}):
        result = hatch('python', 'install', dist_name)

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        f"""
        Incompatible distributions: {dist_name}
        """
    )

    install.assert_not_called()
    path_append.assert_not_called()


def test_incompatible_all(hatch, helpers, path_append, platform, mocker):
    install = mocker.patch('hatch.python.core.PythonManager.install')

    with EnvVars({f'HATCH_PYTHON_VARIANT_{platform.name.upper()}': 'foo'}):
        result = hatch('python', 'install', 'all')

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        f"""
        Incompatible distributions: {', '.join(ORDERED_DISTRIBUTIONS)}
        """
    )

    install.assert_not_called()
    path_append.assert_not_called()


@pytest.mark.requires_internet
def test_installation(
    hatch, helpers, temp_dir_data, platform, path_append, default_shells, compatible_python_distributions
):
    selection = [name for name in compatible_python_distributions if not name.startswith('pypy')]
    dist_name = secrets.choice(selection)
    result = hatch('python', 'install', dist_name)

    install_dir = temp_dir_data / 'data' / 'pythons' / dist_name
    metadata_file = install_dir / InstalledDistribution.metadata_filename()
    python_path = install_dir / json.loads(metadata_file.read_text())['python_path']

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Installing {dist_name}
        Installed {dist_name} @ {install_dir}

        The following directory has been added to your PATH (pending a shell restart):

        {python_path.parent}
        """
    )

    assert python_path.is_file()

    output = platform.check_command_output([python_path, '-c', 'import sys;print(sys.executable)']).strip()
    assert output == str(python_path)

    output = platform.check_command_output([python_path, '--version']).strip()
    assert output.startswith(f'Python {dist_name}.')

    path_append.assert_called_once_with(str(python_path.parent), shells=default_shells)


def test_already_installed_latest(hatch, helpers, temp_dir_data, path_append, dist_name, mocker):
    install = mocker.patch('hatch.python.core.PythonManager.install')
    install_dir = temp_dir_data / 'data' / 'pythons'
    helpers.write_distribution(install_dir, dist_name)

    result = hatch('python', 'install', dist_name)

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        The latest version is already installed: {dist_name}
        """
    )

    install.assert_not_called()
    path_append.assert_not_called()


def test_already_installed_update_disabled(hatch, helpers, temp_dir_data, path_append, dist_name, mocker):
    install = mocker.patch('hatch.python.core.PythonManager.install')
    install_dir = temp_dir_data / 'data' / 'pythons'
    helpers.write_distribution(install_dir, dist_name)
    helpers.downgrade_distribution_metadata(install_dir / dist_name)

    result = hatch('python', 'install', dist_name, input='n\n')

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        f"""
        Update {dist_name}? [y/N]: n
        Distribution is already installed: {dist_name}
        """
    )

    install.assert_not_called()
    path_append.assert_not_called()


def test_already_installed_update_prompt(hatch, helpers, temp_dir_data, path_append, default_shells, dist_name, mocker):
    install_dir = temp_dir_data / 'data' / 'pythons'
    helpers.write_distribution(install_dir, dist_name)

    dist_dir = install_dir / dist_name
    metadata = helpers.downgrade_distribution_metadata(dist_dir)
    python_path = dist_dir / metadata['python_path']
    install = mocker.patch(
        'hatch.python.core.PythonManager.install', return_value=mocker.MagicMock(path=dist_dir, python_path=python_path)
    )

    result = hatch('python', 'install', dist_name, input='y\n')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Update {dist_name}? [y/N]: y
        Updating {dist_name}
        Updated {dist_name} @ {dist_dir}

        The following directory has been added to your PATH (pending a shell restart):

        {python_path.parent}
        """
    )

    install.assert_called_once_with(dist_name)
    path_append.assert_called_once_with(str(python_path.parent), shells=default_shells)


def test_already_installed_update_flag(hatch, helpers, temp_dir_data, path_append, default_shells, dist_name, mocker):
    install_dir = temp_dir_data / 'data' / 'pythons'
    helpers.write_distribution(install_dir, dist_name)

    dist_dir = install_dir / dist_name
    metadata = helpers.downgrade_distribution_metadata(dist_dir)
    python_path = dist_dir / metadata['python_path']
    install = mocker.patch(
        'hatch.python.core.PythonManager.install', return_value=mocker.MagicMock(path=dist_dir, python_path=python_path)
    )

    result = hatch('python', 'install', '--update', dist_name)

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Updating {dist_name}
        Updated {dist_name} @ {dist_dir}

        The following directory has been added to your PATH (pending a shell restart):

        {python_path.parent}
        """
    )

    install.assert_called_once_with(dist_name)
    path_append.assert_called_once_with(str(python_path.parent), shells=default_shells)


@pytest.mark.parametrize('detector', ['in_current_path', 'in_new_path'])
def test_already_in_path(hatch, helpers, temp_dir_data, path_append, mocker, detector, dist_name):
    mocker.patch(f'userpath.{detector}', return_value=True)
    dist_dir = temp_dir_data / 'data' / 'pythons' / dist_name
    python_path = dist_dir / get_distribution(dist_name).python_path
    install = mocker.patch(
        'hatch.python.core.PythonManager.install', return_value=mocker.MagicMock(path=dist_dir, python_path=python_path)
    )

    result = hatch('python', 'install', dist_name)

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Installing {dist_name}
        Installed {dist_name} @ {dist_dir}
        """
    )

    install.assert_called_once_with(dist_name)
    path_append.assert_not_called()


def test_private(hatch, helpers, temp_dir_data, path_append, dist_name, mocker):
    dist_dir = temp_dir_data / 'data' / 'pythons' / dist_name
    python_path = dist_dir / get_distribution(dist_name).python_path
    install = mocker.patch(
        'hatch.python.core.PythonManager.install', return_value=mocker.MagicMock(path=dist_dir, python_path=python_path)
    )

    result = hatch('python', 'install', '--private', dist_name)

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Installing {dist_name}
        Installed {dist_name} @ {dist_dir}
        """
    )

    install.assert_called_once_with(dist_name)
    path_append.assert_not_called()


def test_specific_location(hatch, helpers, temp_dir_data, path_append, dist_name, mocker):
    install_dir = temp_dir_data / 'foo' / 'bar' / 'baz'
    dist_dir = install_dir / dist_name
    python_path = dist_dir / get_distribution(dist_name).python_path
    install = mocker.patch(
        'hatch.python.core.PythonManager.install', return_value=mocker.MagicMock(path=dist_dir, python_path=python_path)
    )

    result = hatch('python', 'install', '--private', '-d', str(install_dir), dist_name)

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Installing {dist_name}
        Installed {dist_name} @ {dist_dir}
        """
    )

    install.assert_called_once_with(dist_name)
    path_append.assert_not_called()


def test_all(hatch, temp_dir_data, path_append, default_shells, mocker, compatible_python_distributions):
    mocked_dists = []
    for name in compatible_python_distributions:
        dist_dir = temp_dir_data / 'data' / 'pythons' / name
        python_path = dist_dir / get_distribution(name).python_path
        mocked_dists.append(mocker.MagicMock(path=dist_dir, python_path=python_path))

    install = mocker.patch('hatch.python.core.PythonManager.install', side_effect=mocked_dists)

    result = hatch('python', 'install', 'all')

    assert result.exit_code == 0, result.output

    expected_lines = []
    for dist in mocked_dists:
        expected_lines.extend((f'Installing {dist.path.name}', f'Installed {dist.path.name} @ {dist.path}'))

    expected_lines.extend((
        '',
        'The following directories have been added to your PATH (pending a shell restart):',
        '',
    ))
    expected_lines.extend(str(dist.python_path.parent) for dist in mocked_dists)
    expected_lines.append('')

    assert result.output == '\n'.join(expected_lines)

    assert install.call_args_list == [mocker.call(name) for name in compatible_python_distributions]
    assert path_append.call_args_list == [
        mocker.call(str(dist.python_path.parent), shells=default_shells) for dist in mocked_dists
    ]
