import pytest

from hatch.errors import PythonDistributionResolutionError, PythonDistributionUnknownError
from hatch.python.resolve import get_distribution
from hatch.utils.structures import EnvVars


class TestErrors:
    def test_unknown_distribution(self):
        with pytest.raises(PythonDistributionUnknownError, match='Unknown distribution: foo'):
            get_distribution('foo')

    def test_resolution_error(self, platform):
        with EnvVars({f'HATCH_PYTHON_VARIANT_{platform.name.upper()}': 'foo'}), pytest.raises(
            PythonDistributionResolutionError,
            match=f"Could not find a default source for name='3.11' system='{platform.name}' arch=",
        ):
            get_distribution('3.11')


class TestDistributionVersions:
    def test_cpython_standalone(self):
        url = 'https://github.com/indygreg/python-build-standalone/releases/download/20230507/cpython-3.11.3%2B20230507-aarch64-unknown-linux-gnu-install_only.tar.gz'
        dist = get_distribution('3.11', url)
        version = dist.version

        assert version.epoch == 0
        assert version.base_version == '3.11.3'

    def test_pypy(self):
        url = 'https://downloads.python.org/pypy/pypy3.10-v7.3.12-aarch64.tar.bz2'
        dist = get_distribution('pypy3.10', url)
        version = dist.version

        assert version.epoch == 0
        assert version.base_version == '7.3.12'


@pytest.mark.parametrize(
    ('system', 'variant'),
    [
        ('windows', 'shared'),
        ('windows', 'static'),
        ('linux', 'v1'),
        ('linux', 'v2'),
        ('linux', 'v3'),
        ('linux', 'v4'),
    ],
)
def test_variants(platform, system, variant):
    if platform.name != system:
        pytest.skip(f'Skipping test for: {system}')

    with EnvVars({f'HATCH_PYTHON_VARIANT_{system.upper()}': variant}):
        dist = get_distribution('3.11')

    if system == 'linux' and variant == 'v1':
        assert variant not in dist.source
    else:
        assert variant in dist.source
