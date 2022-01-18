from ast import literal_eval


def get_python_data(platform, executable='python'):
    process = platform.check_command([executable, '-W', 'ignore', '-'], capture_output=True, input=PYTHON_DATA_SCRIPT)

    return literal_eval(process.stdout.strip().decode('utf-8'))


# Keep support for Python 2 for a while:
# https://github.com/pypa/packaging/blob/20.9/packaging/markers.py#L267-L300
PYTHON_DATA_SCRIPT = b"""\
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
