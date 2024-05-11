import sys
from io import StringIO
from platform import machine
from unittest.mock import patch

import pytest

from hatch.errors import PythonDistributionResolutionError, PythonDistributionUnknownError
from hatch.python.resolve import get_distribution
from hatch.utils.structures import EnvVars


class TestErrors:
    def test_unknown_distribution(self):
        with pytest.raises(PythonDistributionUnknownError, match='Unknown distribution: foo'):
            get_distribution('foo')

    @pytest.mark.skipif(
        not (sys.platform == 'linux' and machine().lower() == 'x86_64'),
        reason='No variants for this platform and architecture combination',
    )
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
        ('linux', 'v1'),
        ('linux', 'v2'),
        ('linux', 'v3'),
        ('linux', 'v4'),
    ],
)
def test_variants(platform, system, variant, current_arch):
    if platform.name != system:
        pytest.skip(f'Skipping test for: {system}')

    with EnvVars({f'HATCH_PYTHON_VARIANT_{system.upper()}': variant}):
        dist = get_distribution('3.11')

    if system == 'linux' and (current_arch != 'x86_64' or variant == 'v1'):
        assert variant not in dist.source
    else:
        assert variant in dist.source


# Intel Core i5-5300U
V3_FLAGS = 'flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch cpuid_fault epb invpcid_single pti ssbd ibrs ibpb stibp tpr_shadow flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm rdseed adx smap intel_pt xsaveopt dtherm ida arat pln pts vnmi md_clear flush_l1d'
# Intel Core i7-860
V2_FLAGS = 'flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ht tm pbe syscall nx rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni dtes64 monitor ds_cpl smx est tm2 ssse3 cx16 xtpr pdcm sse4_1 sse4_2 popcnt lahf_lm pti ssbd ibrs ibpb stibp dtherm ida flush_l1d'
# Just guessing here...
V1_FLAGS = 'flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ht tm pbe syscall nx rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni dtes64 monitor ds_cpl smx est tm2'


class MockFlags:
    def __init__(self, text):
        self.text = text

    def __call__(self, path, *_, **__):
        assert path == '/proc/cpuinfo'
        return StringIO(self.text)


@pytest.mark.skipif(
    not (sys.platform == 'linux' and machine().lower() == 'x86_64'),
    reason='No variants for this platform and architecture combination',
)
def test_guess_variant():
    with EnvVars({'HATCH_PYTHON_VARIANT_LINUX': ''}):
        with patch('hatch.python.resolve.open', MockFlags(V3_FLAGS)):
            dist = get_distribution('3.11')
            assert 'v3' in dist.source
        with patch('hatch.python.resolve.open', MockFlags(V2_FLAGS)):
            dist = get_distribution('3.11')
            assert 'v2' in dist.source
        with patch('hatch.python.resolve.open', MockFlags(V1_FLAGS)):
            dist = get_distribution('3.11')
            assert 'v1' not in dist.source
            assert 'v2' not in dist.source
            assert 'v3' not in dist.source
            assert 'v4' not in dist.source
