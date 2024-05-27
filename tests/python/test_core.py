import json

import pytest

from hatch.config.constants import PythonEnvVars
from hatch.python.core import InstalledDistribution, PythonManager
from hatch.python.distributions import ORDERED_DISTRIBUTIONS
from hatch.python.resolve import custom_env_var, get_distribution
from hatch.utils.structures import EnvVars


@pytest.mark.parametrize('name', ORDERED_DISTRIBUTIONS)
def test_custom_source(platform, current_arch, name):
    if platform.name == 'macos' and current_arch == 'arm64' and name == '3.7':
        pytest.skip('No macOS 3.7 distribution for ARM')

    dist = get_distribution(name)
    with EnvVars({custom_env_var(PythonEnvVars.CUSTOM_SOURCE_PREFIX, name): 'foo'}):
        assert dist.source == 'foo'


@pytest.mark.requires_internet
@pytest.mark.parametrize('name', ORDERED_DISTRIBUTIONS)
def test_installation(temp_dir, platform, current_arch, name):
    if platform.name == 'macos' and current_arch == 'arm64' and name == '3.7':
        pytest.skip('No macOS 3.7 distribution for ARM')

    # Ensure the source and any parent directories get created
    manager = PythonManager(temp_dir / 'foo' / 'bar')
    dist = manager.install(name)

    python_path = dist.python_path
    assert python_path.is_file()

    output = platform.check_command_output([python_path, '-c', 'import sys;print(sys.executable)']).strip()
    assert output == str(python_path)

    major_minor = name.replace('pypy', '')

    output = platform.check_command_output([python_path, '--version']).strip()

    assert output.startswith(f'Python {major_minor}.')
    if name.startswith('pypy'):
        assert 'PyPy' in output


class TestGetInstalled:
    def test_source_does_not_exist(self, temp_dir):
        manager = PythonManager(temp_dir / 'foo')

        assert manager.get_installed() == {}

    def test_not_a_directory(self, temp_dir):
        manager = PythonManager(temp_dir)

        dist = get_distribution('3.10')
        path = temp_dir / dist.name
        path.touch()

        assert manager.get_installed() == {}

    def test_no_metadata_file(self, temp_dir):
        manager = PythonManager(temp_dir)

        dist = get_distribution('3.10')
        path = temp_dir / dist.name
        path.mkdir()

        assert manager.get_installed() == {}

    def test_no_python_path(self, temp_dir):
        manager = PythonManager(temp_dir)

        dist = get_distribution('3.10')
        path = temp_dir / dist.name
        path.mkdir()
        metadata_file = path / InstalledDistribution.metadata_filename()
        metadata_file.write_text(json.dumps({'source': dist.source}))

        assert manager.get_installed() == {}

    def test_order(self, temp_dir, compatible_python_distributions):
        manager = PythonManager(temp_dir)

        for name in compatible_python_distributions:
            dist = get_distribution(name)
            path = temp_dir / dist.name
            path.mkdir()
            metadata_file = path / InstalledDistribution.metadata_filename()
            metadata_file.write_text(json.dumps({'source': dist.source}))
            python_path = path / dist.python_path
            python_path.parent.ensure_dir_exists()
            python_path.touch()

        assert tuple(manager.get_installed()) == compatible_python_distributions
