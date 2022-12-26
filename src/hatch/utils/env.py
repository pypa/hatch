from __future__ import annotations

from ast import literal_eval
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hatch.utils.platform import Platform


class PythonInfo:
    def __init__(self, platform: Platform, executable: str = 'python') -> None:
        self.platform = platform
        self.executable = executable

        self.__dep_check_data: dict[str, Any] | None = None
        self.__environment: dict[str, str] | None = None
        self.__sys_path: list[str] | None = None

    @property
    def dep_check_data(self) -> dict[str, Any]:
        if self.__dep_check_data is None:
            process = self.platform.check_command(
                [self.executable, '-W', 'ignore', '-'], capture_output=True, input=DEP_CHECK_DATA_SCRIPT
            )

            self.__dep_check_data = literal_eval(process.stdout.strip().decode('utf-8'))

        return self.__dep_check_data

    @property
    def environment(self) -> dict[str, str]:
        if self.__environment is None:
            self.__environment = self.dep_check_data['environment']

        return self.__environment

    @property
    def sys_path(self) -> list[str]:
        if self.__sys_path is None:
            self.__sys_path = self.dep_check_data['sys_path']

        return self.__sys_path


# Keep support for Python 2 for a while:
# https://github.com/pypa/packaging/blob/20.9/packaging/markers.py#L267-L300
DEP_CHECK_DATA_SCRIPT = b"""\
import os
import platform
import sys

if hasattr(sys, 'implementation'):
    info = sys.implementation.version
    iver = '{0.major}.{0.minor}.{0.micro}'.format(info)
    kind = info.releaselevel
    if kind != 'final':
        iver += kind[0] + str(info.serial)
    implementation_name = sys.implementation.name
else:
    iver = '0'
    implementation_name = ''

environment = {
    'implementation_name': implementation_name,
    'implementation_version': iver,
    'os_name': os.name,
    'platform_machine': platform.machine(),
    'platform_python_implementation': platform.python_implementation(),
    'platform_release': platform.release(),
    'platform_system': platform.system(),
    'platform_version': platform.version(),
    'python_full_version': platform.python_version(),
    'python_version': '.'.join(platform.python_version_tuple()[:2]),
    'sys_platform': sys.platform,
}
sys_path = [path for path in sys.path if path]

print({'environment': environment, 'sys_path': sys_path})
"""
