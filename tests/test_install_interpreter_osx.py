import pytest
from click.testing import CliRunner
from hatch.cli import hatch
from hatch.interpreters_osx import PYTHON_PKGS_DEFAULT_PATHS, strip_build_ver, ENCODING, is_pkgs_installed
import subprocess

"""
Allow no sudo passwd for tests
sudo echo "$USER  ALL=(ALL) NOPASSWD:/usr/sbin/pkgutil,/bin/rmdir,/bin/rm,/usr/sbin/installer" | sudo tee -a /etc/sudoers
"""

RUNNER = CliRunner()

def install_python(ver):
    return RUNNER.invoke(hatch, ['python', ver])

def uninstall_python(ver):
    return RUNNER.invoke(hatch, ['python', ver, '--rm'])

def runtime(ver):
    command = [PYTHON_PKGS_DEFAULT_PATHS['framework'] +
               '/Versions/' + strip_build_ver(ver) +
               '/bin/python' + strip_build_ver(ver) + ' -c "import sys; print(sys.executable)"']

    installed_in_paths = [
        '/Library/Frameworks/Python.framework/Versions/' \
        + strip_build_ver(ver) + \
        '/bin/python' + strip_build_ver(ver) + '\n',

        '/Library/Frameworks/Python.framework/Versions/'
        + strip_build_ver(ver) + '/Resources/Python.app/Contents/MacOS/Python' + '\n'
    ] #TODO: What is the problem behind installing some versions of python as app, and some as Framework?
      #TODO: Check DEFAULT symlinks is not changed, for example 2.7.14rc1 changes python2.7 symlink
    return any([subprocess.run(command,
                          stdout=subprocess.PIPE,
                          shell=True).stdout.decode(ENCODING) in installed_in_paths])


def no_runtime(ver):
    command = [PYTHON_PKGS_DEFAULT_PATHS['framework'] +
               '/Versions/' + strip_build_ver(ver) +
               '/bin/python' + strip_build_ver(ver) + ' -c "import sys; print(sys.executable)"']
    return 127 == subprocess.run(command,
                                 stdout=subprocess.PIPE,
                                 shell=True).returncode

@pytest.mark.darwin
@pytest.mark.parametrize('ver', ['3.6.0', '2.7.14rc1'])
def test_install_uninstall_python(ver):
    install_python(ver)
    assert runtime(ver)
    assert uninstall_python(ver).exit_code == 0
    assert no_runtime(ver)
    assert not is_pkgs_installed(ver)
