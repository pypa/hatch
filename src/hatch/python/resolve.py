from __future__ import annotations

import os
import platform
import sys
from abc import ABC, abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING

from hatch.config.constants import PythonEnvVars
from hatch.errors import PythonDistributionResolutionError, PythonDistributionUnknownError
from hatch.python.distributions import DISTRIBUTIONS, ORDERED_DISTRIBUTIONS

if TYPE_CHECKING:
    from packaging.version import Version

    from hatch.utils.fs import Path


# Use an artificially high epoch to ensure that custom distributions are always considered newer
CUSTOM_DISTRIBUTION_VERSION_EPOCH = 100


def custom_env_var(prefix: str, name: str) -> str:
    return f'{prefix}{name.upper().replace(".", "_")}'


def get_custom_source(name: str) -> str | None:
    return os.environ.get(custom_env_var(PythonEnvVars.CUSTOM_SOURCE_PREFIX, name))


def get_custom_version(name: str) -> str | None:
    return os.environ.get(custom_env_var(PythonEnvVars.CUSTOM_VERSION_PREFIX, name))


def get_custom_path(name: str) -> str | None:
    return os.environ.get(custom_env_var(PythonEnvVars.CUSTOM_PATH_PREFIX, name))


class Distribution(ABC):
    def __init__(self, name: str, source: str) -> None:
        self.__name = name
        self.__source = source

    @property
    def name(self) -> str:
        return self.__name

    @cached_property
    def source(self) -> str:
        return self.__source if (custom_source := get_custom_source(self.name)) is None else custom_source

    @cached_property
    def archive_name(self) -> str:
        return self.source.rsplit('/', 1)[-1]

    def unpack(self, archive: Path, directory: Path) -> None:
        if self.source.endswith('.zip'):
            import zipfile

            with zipfile.ZipFile(archive, 'r') as zf:
                zf.extractall(directory)
        elif self.source.endswith(('.tar.gz', '.tgz')):
            import tarfile

            with tarfile.open(archive, 'r:gz') as tf:
                if sys.version_info[:2] >= (3, 12):
                    tf.extractall(directory, filter='data')
                else:
                    tf.extractall(directory)  # noqa: S202
        elif self.source.endswith(('.tar.bz2', '.bz2')):
            import tarfile

            with tarfile.open(archive, 'r:bz2') as tf:
                if sys.version_info[:2] >= (3, 12):
                    tf.extractall(directory, filter='data')
                else:
                    tf.extractall(directory)  # noqa: S202
        elif self.source.endswith(('.tar.zst', '.tar.zstd')):
            import tarfile

            import zstandard

            with open(archive, 'rb') as ifh:
                dctx = zstandard.ZstdDecompressor()
                with dctx.stream_reader(ifh) as reader, tarfile.open(mode='r|', fileobj=reader) as tf:
                    if sys.version_info[:2] >= (3, 12):
                        tf.extractall(directory, filter='data')
                    else:
                        tf.extractall(directory)  # noqa: S202
        else:
            message = f'Unknown archive type: {archive}'
            raise ValueError(message)

    @property
    @abstractmethod
    def version(self) -> Version:
        pass

    @property
    @abstractmethod
    def python_path(self) -> str:
        pass


class CPythonStandaloneDistribution(Distribution):
    @cached_property
    def version(self) -> Version:
        from packaging.version import Version

        if (custom_version := get_custom_version(self.name)) is not None:
            return Version(f'{CUSTOM_DISTRIBUTION_VERSION_EPOCH}!{custom_version}')

        # .../cpython-3.12.0%2B20231002-...
        # .../cpython-3.7.9-...
        _, _, remaining = self.source.partition('/cpython-')
        # 3.12.0%2B20231002-...
        # 3.7.9-...
        version = remaining.split('%2B')[0] if '%2B' in remaining else remaining.split('-')[0]
        return Version(f'0!{version}')

    @cached_property
    def python_path(self) -> str:
        if (custom_path := get_custom_path(self.name)) is not None:
            return custom_path

        if self.name == '3.7':
            if sys.platform == 'win32':
                return r'python\install\python.exe'

            return 'python/install/bin/python3'

        if sys.platform == 'win32':
            return r'python\python.exe'

        return 'python/bin/python3'


class PyPyOfficialDistribution(Distribution):
    @cached_property
    def version(self) -> Version:
        from packaging.version import Version

        if (custom_version := get_custom_version(self.name)) is not None:
            return Version(f'{CUSTOM_DISTRIBUTION_VERSION_EPOCH}!{custom_version}')

        *_, remaining = self.source.partition('/pypy/')
        _, version, *_ = remaining.split('-')
        return Version(f'0!{version[1:]}')

    @cached_property
    def python_path(self) -> str:
        if (custom_path := get_custom_path(self.name)) is not None:
            return custom_path

        directory = self.archive_name
        for extension in ('.tar.bz2', '.zip'):
            if directory.endswith(extension):
                directory = directory[: -len(extension)]
                break

        if sys.platform == 'win32':
            return rf'{directory}\pypy.exe'

        return f'{directory}/bin/pypy'


def get_distribution(name: str, source: str = '', variant_cpu: str = '', variant_gil: str = '') -> Distribution:
    if source:
        return _get_distribution_class(source)(name, source)

    if name not in DISTRIBUTIONS:
        message = f'Unknown distribution: {name}'
        raise PythonDistributionUnknownError(message)

    arch = platform.machine().lower()
    if sys.platform == 'win32':
        system = 'windows'
        abi = 'msvc'
    elif sys.platform == 'darwin':
        system = 'macos'
        abi = ''
    else:
        system = 'linux'
        abi = 'gnu' if any(platform.libc_ver()) else 'musl'

    if not variant_cpu:
        variant_cpu = _get_default_variant_cpu(name, system, arch)

    if not variant_gil:
        variant_gil = _get_default_variant_gil()

    key = (system, arch, abi, variant_cpu, variant_gil)

    keys: dict[tuple, str] = DISTRIBUTIONS[name]
    if key not in keys:
        message = f'Could not find a default source for {name=} {system=} {arch=} {abi=} {variant_cpu=} {variant_gil=}'
        raise PythonDistributionResolutionError(message)

    source = keys[key]
    return _get_distribution_class(source)(name, source)


def get_compatible_distributions() -> dict[str, Distribution]:
    distributions: dict[str, Distribution] = {}
    for name in ORDERED_DISTRIBUTIONS:
        try:
            dist = get_distribution(name)
        except PythonDistributionResolutionError:
            pass
        else:
            distributions[name] = dist

    return distributions


def _guess_linux_variant_cpu() -> str:
    # Use the highest that we know is most common when we can't parse CPU data
    default = 'v3'
    try:
        # Don't use our utility Path so we can properly mock
        with open('/proc/cpuinfo', encoding='utf-8') as f:
            contents = f.read()
    except OSError:
        return default

    # See https://clang.llvm.org/docs/UsersManual.html#x86 for the
    # instructions for each architecture variant and
    # https://github.com/torvalds/linux/blob/master/arch/x86/include/asm/cpufeatures.h
    # for the corresponding Linux flags
    v2_flags = {'cx16', 'lahf_lm', 'popcnt', 'pni', 'sse4_1', 'sse4_2', 'ssse3'}
    v3_flags = {'avx', 'avx2', 'bmi1', 'bmi2', 'f16c', 'fma', 'movbe', 'xsave'} | v2_flags
    v4_flags = {'avx512f', 'avx512bw', 'avx512cd', 'avx512dq', 'avx512vl'} | v3_flags

    for line in contents.splitlines():
        key, _, value = line.partition(':')
        if key.strip() == 'flags':
            flags = set(value.strip().split())

            if flags.issuperset(v4_flags):
                return 'v4'

            if flags.issuperset(v3_flags):
                return 'v3'

            if flags.issuperset(v2_flags):
                return 'v2'

            return 'v1'

    return default


def _get_default_variant_cpu(name: str, system: str, arch: str) -> str:
    # not PyPy
    if name[0].isdigit():
        variant = os.environ.get(
            'HATCH_PYTHON_VARIANT_CPU',
            # Legacy name
            os.environ.get(f'HATCH_PYTHON_VARIANT_{system.upper()}', ''),
        ).lower()

        # https://gregoryszorc.com/docs/python-build-standalone/main/running.html
        if system == 'linux' and arch == 'x86_64':
            # Intel-specific optimizations depending on age of release
            if variant:
                return variant

            if name == '3.8':
                return 'v1'

            if name != '3.7':
                return _guess_linux_variant_cpu()

    return ''


def _get_default_variant_gil() -> str:
    return os.environ.get('HATCH_PYTHON_VARIANT_GIL', '').lower()


def _get_distribution_class(source: str) -> type[Distribution]:
    if source.startswith('https://github.com/indygreg/python-build-standalone/releases/download/'):
        return CPythonStandaloneDistribution

    if source.startswith('https://downloads.python.org/pypy/'):
        return PyPyOfficialDistribution

    message = f'Unknown distribution source: {source}'
    raise ValueError(message)
