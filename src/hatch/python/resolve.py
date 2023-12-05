from __future__ import annotations

import os
import platform
import sys
from abc import ABC, abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING

from hatch.errors import PythonDistributionResolutionError, PythonDistributionUnknownError
from hatch.python.distributions import DISTRIBUTIONS, ORDERED_DISTRIBUTIONS

if TYPE_CHECKING:
    from packaging.version import Version

    from hatch.utils.fs import Path


class Distribution(ABC):
    def __init__(self, name: str, source: str) -> None:
        self.__name = name
        self.__source = source

    @property
    def name(self) -> str:
        return self.__name

    @property
    def source(self) -> str:
        return self.__source

    @cached_property
    def archive_name(self) -> str:
        return self.source.rsplit('/', 1)[-1]

    def unpack(self, archive: Path, directory: Path) -> None:
        if self.source.endswith('.zip'):
            import zipfile

            with zipfile.ZipFile(archive, 'r') as zf:
                zf.extractall(directory)
        elif self.source.endswith('.tar.gz'):
            import tarfile

            with tarfile.open(archive, 'r:gz') as tf:
                tf.extractall(directory)  # noqa: S202
        elif self.source.endswith('.tar.bz2'):
            import tarfile

            with tarfile.open(archive, 'r:bz2') as tf:
                tf.extractall(directory)  # noqa: S202
        elif self.source.endswith('.tar.zst'):
            import tarfile

            import zstandard

            with open(archive, 'rb') as ifh:
                dctx = zstandard.ZstdDecompressor()
                with dctx.stream_reader(ifh) as reader, tarfile.open(mode='r|', fileobj=reader) as tf:
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

        # .../cpython-3.12.0%2B20231002-...
        # .../cpython-3.7.9-...
        _, _, remaining = self.source.partition('/cpython-')
        # 3.12.0%2B20231002-...
        # 3.7.9-...
        version = remaining.split('%2B')[0] if '%2B' in remaining else remaining.split('-')[0]
        return Version(f'0!{version}')

    @cached_property
    def python_path(self) -> str:
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

        *_, remaining = self.source.partition('/pypy/')
        _, version, *_ = remaining.split('-')
        return Version(f'0!{version[1:]}')

    @cached_property
    def python_path(self) -> str:
        directory = self.archive_name
        for extension in ('.tar.bz2', '.zip'):
            if directory.endswith(extension):
                directory = directory[: -len(extension)]
                break

        if sys.platform == 'win32':
            return rf'{directory}\pypy.exe'

        return f'{directory}/bin/pypy'


def get_distribution(name: str, source: str = '', variant: str = '') -> Distribution:
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

    if not variant:
        variant = _get_default_variant(name, system, arch, abi)

    key = (system, arch, abi, variant)

    keys: dict[tuple, str] = DISTRIBUTIONS[name]
    if key not in keys:
        message = f'Could not find a default source for {name=} {system=} {arch=} {abi=} {variant=}'
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


def _get_default_variant(name: str, system: str, arch: str, abi: str) -> str:
    variant = os.environ.get(f'HATCH_PYTHON_VARIANT_{system.upper()}', '').lower()
    if variant:
        return variant

    if name[0].isdigit():
        if system == 'windows' and abi == 'msvc':
            return 'shared'

        if system == 'linux' and arch == 'x86_64':
            if name == '3.8':
                return 'v1'

            if name != '3.7':
                return 'v3'

    return ''


def _get_distribution_class(source: str) -> type[Distribution]:
    if source.startswith('https://github.com/indygreg/python-build-standalone/releases/download/'):
        return CPythonStandaloneDistribution

    if source.startswith('https://downloads.python.org/pypy/'):
        return PyPyOfficialDistribution

    message = f'Unknown distribution source: {source}'
    raise ValueError(message)
