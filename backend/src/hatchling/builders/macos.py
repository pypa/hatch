from __future__ import annotations

import os
import platform
import re

__all__ = ['process_macos_plat_tag']


def process_macos_plat_tag(plat: str, /, *, compat: bool) -> str:
    """
    Process the macOS platform tag. This will normalize the macOS version to
    10.16 if compat=True. If the MACOSX_DEPLOYMENT_TARGET environment variable
    is set, then it will be used instead for the target version.  If archflags
    is set, then the archs will be respected, including a universal build.
    """
    # Default to a native build
    current_arch = platform.machine()
    arm = current_arch == 'arm64'

    # Look for cross-compiles
    archflags = os.environ.get('ARCHFLAGS', '')
    if archflags and (archs := re.findall(r'-arch (\S+)', archflags)):
        new_arch = 'universal2' if set(archs) == {'x86_64', 'arm64'} else archs[0]
        arm = archs == ['arm64']
        plat = f'{plat[: plat.rfind(current_arch)]}{new_arch}'

    # Process macOS version
    if sdk_match := re.search(r'macosx_(\d+_\d+)', plat):
        macos_version = sdk_match.group(1)
        target = os.environ.get('MACOSX_DEPLOYMENT_TARGET', None)

        try:
            new_version = normalize_macos_version(target or macos_version, arm=arm, compat=compat)
        except ValueError:
            new_version = normalize_macos_version(macos_version, arm=arm, compat=compat)

        return plat.replace(macos_version, new_version, 1)

    return plat


def normalize_macos_version(version: str, *, arm: bool, compat: bool) -> str:
    """
    Set minor version to 0 if major is 11+. Enforces 11+ if arm=True. 11+ is
    converted to 10.16 if compat=True. Version is always returned in
    "major_minor" format.
    """
    version = version.replace('.', '_')
    if '_' not in version:
        version = f'{version}_0'
    major, minor = (int(d) for d in version.split('_')[:2])
    major = max(major, 11) if arm else major
    minor = 0 if major >= 11 else minor  # noqa: PLR2004
    if compat and major >= 11:  # noqa: PLR2004
        major = 10
        minor = 16
    return f'{major}_{minor}'
