import json
import os
import shutil
import subprocess
import sys
import time
from contextlib import suppress
from functools import lru_cache
from typing import Generator, NamedTuple

import pytest
from click.testing import CliRunner as __CliRunner
from filelock import FileLock
from platformdirs import user_cache_dir, user_data_dir

from hatch.config.constants import AppEnvVars, ConfigEnvVars, PublishEnvVars
from hatch.config.user import ConfigFile
from hatch.utils.ci import running_in_ci
from hatch.utils.fs import Path, temp_directory
from hatch.utils.platform import Platform
from hatch.utils.structures import EnvVars
from hatch.venv.core import TempVirtualEnv
from hatchling.cli import hatchling

from .helpers.templates.licenses import MIT, Apache_2_0

PLATFORM = Platform()


class Devpi(NamedTuple):
    repo: str
    index_name: str
    user: str
    auth: str
    ca_cert: str


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
            PublishEnvVars.REPO: 'dev',
            'HATCH_SELF_TESTING': 'true',
            'PYAPP_COMMAND_NAME': os.urandom(4).hex(),
            'GIT_AUTHOR_NAME': 'Foo Bar',
            'GIT_AUTHOR_EMAIL': 'foo@bar.baz',
            'COLUMNS': '80',
            'LINES': '24',
        }
        if PLATFORM.windows:
            default_env_vars['COMSPEC'] = 'cmd.exe'
        else:
            default_env_vars['SHELL'] = 'sh'

        with d.as_cwd(default_env_vars):
            os.environ.pop(AppEnvVars.ENV_ACTIVE, None)
            os.environ.pop(AppEnvVars.FORCE_COLOR, None)
            yield d


@pytest.fixture(scope='session')
def isolated_data_dir() -> Path:
    return Path(os.environ[ConfigEnvVars.DATA])


@pytest.fixture(scope='session')
def default_data_dir() -> Path:
    return Path(user_data_dir('hatch', appauthor=False))


@pytest.fixture(scope='session')
def default_cache_dir() -> Path:
    return Path(user_cache_dir('hatch', appauthor=False))


@pytest.fixture(scope='session')
def platform():
    return PLATFORM


@pytest.fixture(scope='session')
def current_platform():
    return PLATFORM.name


@pytest.fixture(scope='session')
def uri_slash_prefix():
    return '//' if os.sep == '/' else '///'


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


@pytest.fixture(scope='session')
def default_virtualenv_installed_requirements(helpers):
    # PyPy installs extra packages by default
    with TempVirtualEnv(sys.executable, PLATFORM):
        output = PLATFORM.run_command(['pip', 'freeze'], check=True, capture_output=True).stdout.decode('utf-8')
        requirements = helpers.extract_requirements(output.splitlines())

    return frozenset(requirements)


@pytest.fixture(scope='session')
def extract_installed_requirements(helpers, default_virtualenv_installed_requirements):
    return lambda lines: [
        requirement
        for requirement in helpers.extract_requirements(lines)
        if requirement not in default_virtualenv_installed_requirements
    ]


@pytest.fixture(scope='session', autouse=True)
def python_on_path():
    return Path(sys.executable).stem


@pytest.fixture(scope='session')
def compatible_python_distributions():
    from hatch.python.resolve import get_compatible_distributions

    return tuple(get_compatible_distributions())


@pytest.fixture(scope='session')
def devpi(tmp_path_factory, worker_id):
    import platform

    if not shutil.which('docker') or (
        running_in_ci() and (not PLATFORM.linux or platform.python_implementation() == 'PyPy')
    ):
        pytest.skip('Not testing publishing')

    # This fixture is affected by https://github.com/pytest-dev/pytest-xdist/issues/271
    root_tmp_dir = Path(tmp_path_factory.getbasetemp().parent)

    devpi_data_file = root_tmp_dir / 'devpi_data.json'
    lock_file = f'{devpi_data_file}.lock'
    devpi_started_sessions = root_tmp_dir / 'devpi_started_sessions'
    devpi_ended_sessions = root_tmp_dir / 'devpi_ended_sessions'
    devpi_data = root_tmp_dir / 'devpi_data'
    devpi_docker_data = devpi_data / 'docker'
    with FileLock(lock_file):
        if devpi_data_file.is_file():
            data = json.loads(devpi_data_file.read_text())
        else:
            import trustme

            devpi_started_sessions.mkdir()
            devpi_ended_sessions.mkdir()
            devpi_data.mkdir()

            shutil.copytree(Path(__file__).resolve().parent / 'index' / 'server', devpi_docker_data)

            # https://github.com/python-trio/trustme/blob/master/trustme/_cli.py
            # Generate the CA certificate
            ca = trustme.CA()
            cert = ca.issue_cert('localhost', '127.0.0.1', '::1')

            # Write the certificate and private key the server should use
            server_config_dir = devpi_docker_data / 'nginx'
            server_key = str(server_config_dir / 'server.key')
            server_cert = str(server_config_dir / 'server.pem')
            cert.private_key_pem.write_to_path(path=server_key)
            with open(server_cert, mode='w', encoding='utf-8') as f:
                f.truncate()
            for blob in cert.cert_chain_pems:
                blob.write_to_path(path=server_cert, append=True)

            # Write the certificate the client should trust
            client_cert = str(devpi_data / 'client.pem')
            ca.cert_pem.write_to_path(path=client_cert)

            data = {'password': os.urandom(16).hex(), 'ca_cert': client_cert}
            devpi_data_file.write_atomic(json.dumps(data), 'w', encoding='utf-8')

    dp = Devpi('https://localhost:8443/hatch/testing/', 'testing', 'hatch', data['password'], data['ca_cert'])
    env_vars = {'DEVPI_INDEX_NAME': dp.index_name, 'DEVPI_USERNAME': dp.user, 'DEVPI_PASSWORD': dp.auth}

    compose_file = str(devpi_docker_data / 'docker-compose.yaml')
    with FileLock(lock_file):
        if not any(devpi_started_sessions.iterdir()):
            with EnvVars(env_vars):
                subprocess.check_call(['docker', 'compose', '-f', compose_file, 'up', '--build', '-d'])

            for _ in range(60):
                output = subprocess.check_output(['docker', 'logs', 'hatch-devpi']).decode('utf-8')
                if f'Serving index {dp.user}/{dp.index_name}' in output:
                    time.sleep(5)
                    break

                time.sleep(1)
            else:  # no cov
                pass

        (devpi_started_sessions / worker_id).touch()

    try:
        yield dp
    finally:
        with FileLock(lock_file):
            (devpi_ended_sessions / worker_id).touch()
            if len(list(devpi_started_sessions.iterdir())) == len(list(devpi_ended_sessions.iterdir())):
                devpi_data_file.unlink()
                shutil.rmtree(devpi_started_sessions)
                shutil.rmtree(devpi_ended_sessions)

                with EnvVars(env_vars):
                    subprocess.run(['docker', 'compose', '-f', compose_file, 'down', '-t', '0'], capture_output=True)  # noqa: PLW1510

                shutil.rmtree(devpi_data)


@pytest.fixture
def mock_backend_process(request, mocker):
    if 'allow_backend_process' in request.keywords:
        yield False
        return

    def mock_process_api(api):
        def mock_process(command, **kwargs):
            if not isinstance(command, list) or command[1:4] != ['-u', '-m', 'hatchling']:  # no cov
                return api(command, **kwargs)

            original_args = sys.argv
            try:
                sys.argv = command[3:]
                mock = mocker.MagicMock()

                try:
                    # The builder sets process-wide environment variables
                    with EnvVars():
                        hatchling()
                except SystemExit as e:
                    mock.returncode = e.code
                else:
                    mock.returncode = 0

                return mock
            finally:
                sys.argv = original_args

        return mock_process

    mocker.patch('hatch.utils.platform.Platform.run_command', side_effect=mock_process_api(PLATFORM.run_command))

    yield True


@pytest.fixture
def mock_backend_process_output(request, mocker):
    if 'allow_backend_process' in request.keywords:
        yield False
        return

    output_queue = []

    def mock_process_api(api):
        def mock_process(command, **kwargs):
            if not isinstance(command, list) or command[1:4] != ['-u', '-m', 'hatchling']:  # no cov
                return api(command, **kwargs)

            output_queue.clear()
            original_args = sys.argv
            try:
                sys.argv = command[3:]
                mock = mocker.MagicMock()

                try:
                    # The builder sets process-wide environment variables
                    with EnvVars():
                        hatchling()
                except SystemExit as e:
                    mock.returncode = e.code
                else:
                    mock.returncode = 0

                mock.stdout = ''.join(output_queue).encode('utf-8')
                return mock
            finally:
                sys.argv = original_args

        return mock_process

    mocker.patch('subprocess.run', side_effect=mock_process_api(subprocess.run))
    mocker.patch('hatchling.bridge.app._display', side_effect=lambda cmd: output_queue.append(f'{cmd}\n'))

    yield True


@pytest.fixture
def mock_plugin_installation(mocker):
    subprocess_run = subprocess.run
    mocked_subprocess_run = mocker.MagicMock(returncode=0)

    def _mock(command, **kwargs):
        if not isinstance(command, list) or command[:5] != [sys.executable, '-u', '-m', 'pip', 'install']:  # no cov
            return subprocess_run(command, **kwargs)

        mocked_subprocess_run(command, **kwargs)
        return mocked_subprocess_run

    mocker.patch('subprocess.run', side_effect=_mock)

    return mocked_subprocess_run


@pytest.fixture
def local_backend_process(mock_backend_process, mocker):
    if mock_backend_process:
        mocker.patch('hatch.env.virtual.VirtualEnvironment.build_environment')

    return mock_backend_process


@pytest.fixture
def local_backend_process_output(mock_backend_process_output, mocker):
    if mock_backend_process_output:
        mocker.patch('hatch.env.virtual.VirtualEnvironment.build_environment')

    return mock_backend_process_output


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

        if marker.name == 'requires_unix' and PLATFORM.windows:
            pytest.skip('Not running on a Linux-based platform')

        if marker.name == 'requires_git' and not shutil.which('git'):
            pytest.skip('Git not present in the environment')


def pytest_configure(config):
    config.addinivalue_line('markers', 'requires_windows: Tests intended for Windows operating systems')
    config.addinivalue_line('markers', 'requires_macos: Tests intended for macOS operating systems')
    config.addinivalue_line('markers', 'requires_linux: Tests intended for Linux operating systems')
    config.addinivalue_line('markers', 'requires_unix: Tests intended for Linux-based operating systems')
    config.addinivalue_line('markers', 'requires_internet: Tests that require access to the internet')
    config.addinivalue_line('markers', 'requires_git: Tests that require the git command available in the environment')

    config.addinivalue_line('markers', 'allow_backend_process: Force the use of backend communication')

    config.getini('norecursedirs').remove('build')  # /tests/cli/build
    config.getini('norecursedirs').remove('venv')  # /tests/venv


@lru_cache
def network_connectivity():  # no cov
    if running_in_ci():
        return True

    import socket

    with suppress(Exception):
        # Test availability of DNS first
        host = socket.gethostbyname('www.google.com')
        # Test connection
        socket.create_connection((host, 80), 2)
        return True

    return False
