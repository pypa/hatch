import sys
from platform import machine

import pytest

from hatch.config.constants import PythonEnvVars
from hatch.errors import PythonDistributionResolutionError, PythonDistributionUnknownError
from hatch.python.resolve import custom_env_var, get_distribution
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
        with (
            EnvVars({'HATCH_PYTHON_VARIANT_CPU': 'foo'}),
            pytest.raises(
                PythonDistributionResolutionError,
                match=f"Could not find a default source for name='3.11' system='{platform.name}' arch=",
            ),
        ):
            get_distribution('3.11')


class TestDistributionVersions:
    def test_cpython_standalone(self):
        url = 'https://github.com/astral-sh/python-build-standalone/releases/download/20230507/cpython-3.11.3%2B20230507-aarch64-unknown-linux-gnu-install_only.tar.gz'
        dist = get_distribution('3.11', url)
        version = dist.version

        assert version.epoch == 0
        assert version.base_version == '3.11.3'

    def test_cpython_standalone_from_legacy_link(self) -> None:
        url = 'https://github.com/indygreg/python-build-standalone/releases/download/20230507/cpython-3.11.3%2B20230507-aarch64-unknown-linux-gnu-install_only.tar.gz'
        dist = get_distribution('3.11', url)
        version = dist.version

        assert version.epoch == 0
        assert version.base_version == '3.11.3'

    def test_cpython_standalone_custom(self):
        name = '3.11'
        dist = get_distribution(name)
        with EnvVars({custom_env_var(PythonEnvVars.CUSTOM_VERSION_PREFIX, name): '9000.42'}):
            version = dist.version

        assert version.epoch == 100
        assert '.'.join(map(str, version.release)) == '9000.42'

    def test_pypy(self):
        url = 'https://downloads.python.org/pypy/pypy3.10-v7.3.12-aarch64.tar.bz2'
        dist = get_distribution('pypy3.10', url)
        version = dist.version

        assert version.epoch == 0
        assert version.base_version == '7.3.12'

    def test_pypy_custom(self):
        name = 'pypy3.10'
        dist = get_distribution(name)
        with EnvVars({custom_env_var(PythonEnvVars.CUSTOM_VERSION_PREFIX, name): '9000.42'}):
            version = dist.version

        assert version.epoch == 100
        assert '.'.join(map(str, version.release)) == '9000.42'


class TestDistributionPaths:
    def test_cpython_standalone_custom(self):
        name = '3.11'
        dist = get_distribution(name)
        with EnvVars({custom_env_var(PythonEnvVars.CUSTOM_PATH_PREFIX, name): 'foo/bar/python'}):
            assert dist.python_path == 'foo/bar/python'

    def test_pypy_custom(self):
        name = 'pypy3.10'
        dist = get_distribution(name)
        with EnvVars({custom_env_var(PythonEnvVars.CUSTOM_PATH_PREFIX, name): 'foo/bar/python'}):
            assert dist.python_path == 'foo/bar/python'


@pytest.mark.requires_linux
class TestVariantCPU:
    def test_legacy_option(self, current_arch):
        variant = 'v4'
        with EnvVars({'HATCH_PYTHON_VARIANT_LINUX': variant}):
            dist = get_distribution('3.12')

        if current_arch != 'x86_64':
            assert variant not in dist.source
        else:
            assert variant in dist.source

    @pytest.mark.parametrize('variant', ['v1', 'v2', 'v3', 'v4'])
    def test_compatibility(self, variant, current_arch):
        with EnvVars({'HATCH_PYTHON_VARIANT_CPU': variant}):
            dist = get_distribution('3.12')

        if current_arch != 'x86_64' or variant == 'v1':
            assert variant not in dist.source
        else:
            assert variant in dist.source

    @pytest.mark.skipif(
        machine().lower() != 'x86_64',
        reason='No variants for this platform and architecture combination',
    )
    @pytest.mark.parametrize(
        ('variant', 'flags'),
        [
            pytest.param(
                'v1',
                # Just guessing here...
                'flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ht tm pbe syscall nx rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni dtes64 monitor ds_cpl smx est tm2',
                id='v1',
            ),
            pytest.param(
                'v2',
                # Intel Core i7-860
                'flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ht tm pbe syscall nx rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni dtes64 monitor ds_cpl smx est tm2 ssse3 cx16 xtpr pdcm sse4_1 sse4_2 popcnt lahf_lm pti ssbd ibrs ibpb stibp dtherm ida flush_l1d',
                id='v2',
            ),
            pytest.param(
                'v3',
                # Intel Core i5-5300U
                'flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch cpuid_fault epb invpcid_single pti ssbd ibrs ibpb stibp tpr_shadow flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm rdseed adx smap intel_pt xsaveopt dtherm ida arat pln pts vnmi md_clear flush_l1d',
                id='v3',
            ),
            pytest.param(
                'v4',
                # Just guessing here...
                'flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch cpuid_fault epb invpcid_single pti ssbd ibrs ibpb stibp tpr_shadow flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm rdseed adx smap intel_pt xsaveopt dtherm ida arat pln pts vnmi md_clear flush_l1d avx512f avx512bw avx512cd avx512dq avx512vl',
                id='v4',
            ),
        ],
    )
    def test_guess_variant(self, fs, variant, flags):
        fs.create_file('/proc/cpuinfo', contents=flags)

        with EnvVars({'HATCH_PYTHON_VARIANT_CPU': ''}):
            dist = get_distribution('3.12')
            if variant == 'v1':
                for v in ('v1', 'v2', 'v3', 'v4'):
                    assert v not in dist.source
            else:
                assert variant in dist.source


class TestVariantGIL:
    def test_compatible(self):
        with EnvVars({'HATCH_PYTHON_VARIANT_GIL': 'freethreaded'}):
            dist = get_distribution('3.13')

        assert 'freethreaded' in dist.source

    def test_incompatible(self, platform):
        with (
            EnvVars({'HATCH_PYTHON_VARIANT_GIL': 'freethreaded'}),
            pytest.raises(
                PythonDistributionResolutionError,
                match=f"Could not find a default source for name='3.12' system='{platform.name}' arch=",
            ),
        ):
            get_distribution('3.12')
