import os
import subprocess
import sys
from functools import lru_cache
from io import BytesIO
from typing import Generator

import pytest
from click.testing import CliRunner as __CliRunner
from platformdirs import user_cache_dir, user_data_dir

from hatch.config.constants import AppEnvVars, ConfigEnvVars, PublishEnvVars
from hatch.config.user import ConfigFile
from hatch.utils.ci import running_in_ci
from hatch.utils.fs import Path, temp_directory
from hatch.utils.platform import Platform
from hatch.utils.structures import EnvVars
from hatchling.cli import hatchling

from .helpers.templates.licenses import MIT, Apache_2_0

PLATFORM = Platform()


class CliRunner(__CliRunner):
    def __init__(self, command):
        super().__init__()
        self._command = command

    def __call__(self, *args, **kwargs):
        # Exceptions should always be handled
        kwargs.setdefault('catch_exceptions', False)

        return self.invoke(self._command, args, **kwargs)


@pytest.fixture(scope='session')
def hatch():
    from hatch import cli

    return CliRunner(cli.hatch)


@pytest.fixture(scope='session')
def helpers():
    # https://docs.pytest.org/en/latest/writing_plugins.html#assertion-rewriting
    pytest.register_assert_rewrite('tests.helpers.helpers')

    from .helpers import helpers

    return helpers


@pytest.fixture(scope='session', autouse=True)
def isolation() -> Generator[Path, None, None]:
    with temp_directory() as d:
        data_dir = d / 'data'
        data_dir.mkdir()
        cache_dir = d / 'cache'
        cache_dir.mkdir()

        licenses_dir = cache_dir / 'licenses'
        licenses_dir.mkdir()
        licenses_dir.joinpath('Apache-2.0.txt').write_text(Apache_2_0)
        licenses_dir.joinpath('MIT.txt').write_text(MIT)

        default_env_vars = {
            AppEnvVars.NO_COLOR: '1',
            ConfigEnvVars.DATA: str(data_dir),
            ConfigEnvVars.CACHE: str(cache_dir),
            PublishEnvVars.REPO: 'test',
            'GIT_AUTHOR_NAME': 'Foo Bar',
            'GIT_AUTHOR_EMAIL': 'foo@bar.baz',
            'COLUMNS': '80',
            'LINES': '24',
        }
        with d.as_cwd(default_env_vars):
            os.environ.pop(AppEnvVars.ENV_ACTIVE, None)
            yield d


@pytest.fixture(scope='session')
def data_dir() -> Generator[Path, None, None]:
    yield Path(os.environ[ConfigEnvVars.DATA])


@pytest.fixture(scope='session')
def cache_dir() -> Generator[Path, None, None]:
    yield Path(os.environ[ConfigEnvVars.CACHE])


@pytest.fixture(scope='session')
def default_data_dir() -> Generator[Path, None, None]:
    yield Path(user_data_dir('hatch', appauthor=False))


@pytest.fixture(scope='session')
def default_cache_dir() -> Generator[Path, None, None]:
    yield Path(user_cache_dir('hatch', appauthor=False))


@pytest.fixture(scope='session')
def platform():
    return PLATFORM


@pytest.fixture(scope='session')
def current_platform():
    return PLATFORM.name


@pytest.fixture(scope='session')
def legacy_windows_terminal():
    from rich.console import detect_legacy_windows

    return detect_legacy_windows()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    with temp_directory() as d:
        yield d


@pytest.fixture
def temp_dir_data(temp_dir) -> Generator[Path, None, None]:
    data_path = temp_dir / 'data'
    data_path.mkdir()

    with EnvVars({ConfigEnvVars.DATA: str(data_path)}):
        yield temp_dir


@pytest.fixture
def temp_dir_cache(temp_dir) -> Generator[Path, None, None]:
    cache_path = temp_dir / 'cache'
    cache_path.mkdir()

    with EnvVars({ConfigEnvVars.CACHE: str(cache_path)}):
        yield temp_dir


@pytest.fixture(autouse=True)
def config_file(tmp_path) -> ConfigFile:
    path = Path(tmp_path, 'config.toml')
    os.environ[ConfigEnvVars.CONFIG] = str(path)
    config = ConfigFile(path)
    config.restore()
    return config


@pytest.fixture
def mock_backend_process(request, mocker):
    if 'allow_backend_process' in request.keywords:
        yield False
        return

    line_queue = []

    def mock_process_api(api):
        def mock_process(command, **kwargs):
            if not isinstance(command, list) or command[1:4] != ['-u', '-m', 'hatchling']:  # no cov
                return api(command, **kwargs)

            line_queue.clear()
            original_args = sys.argv
            try:
                sys.argv = command[3:]
                mock = mocker.MagicMock()

                try:
                    hatchling()
                except SystemExit as e:
                    mock.returncode = e.code
                else:
                    mock.returncode = 0

                mock.stdout = BytesIO(''.join(line_queue).encode('utf-8'))
                return mock
            finally:
                sys.argv = original_args

        return mock_process

    mocker.patch('subprocess.Popen', side_effect=mock_process_api(subprocess.Popen))
    mocker.patch('subprocess.run', side_effect=mock_process_api(subprocess.run))
    mocker.patch('hatchling.bridge.app._send_app_command', side_effect=lambda cmd: line_queue.append(f'{cmd}\n'))

    yield True


def pytest_runtest_setup(item):
    for marker in item.iter_markers():
        if marker.name == 'requires_internet' and not network_connectivity():  # no cov
            pytest.skip('No network connectivity')

        if marker.name == 'requires_ci' and not running_in_ci():  # no cov
            pytest.skip('Not running in CI')

        if marker.name == 'requires_windows' and not PLATFORM.windows:
            pytest.skip('Not running on Windows')

        if marker.name == 'requires_macos' and not PLATFORM.macos:
            pytest.skip('Not running on macOS')

        if marker.name == 'requires_linux' and not PLATFORM.linux:
            pytest.skip('Not running on Linux')


def pytest_configure(config):
    config.addinivalue_line('markers', 'requires_windows: Tests intended for Windows operating systems')
    config.addinivalue_line('markers', 'requires_macos: Tests intended for macOS operating systems')
    config.addinivalue_line('markers', 'requires_linux: Tests intended for Linux operating systems')
    config.addinivalue_line('markers', 'requires_internet: Tests that require access to the internet')

    config.addinivalue_line('markers', 'allow_backend_process: Force the use of backend communication')

    config.getini('norecursedirs').remove('build')  # /tests/cli/build
    config.getini('norecursedirs').remove('venv')  # /tests/venv


@lru_cache()
def network_connectivity():  # no cov
    if running_in_ci():
        return True

    import socket

    try:
        # Test availability of DNS first
        host = socket.gethostbyname('www.google.com')
        # Test connection
        socket.create_connection((host, 80), 2)
        return True
    except Exception:
        return False
