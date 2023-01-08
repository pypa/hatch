import os
import stat

import pytest

from hatch.utils.fs import Path
from hatch.utils.platform import Platform
from hatch.utils.structures import EnvVars


@pytest.mark.requires_windows
class TestWindows:
    def test_tag(self):
        assert Platform().windows is True

    def test_default_shell(self):
        assert Platform().default_shell == os.environ.get('COMSPEC', 'cmd')

    def test_format_for_subprocess_list(self):
        assert Platform().format_for_subprocess(['foo', 'bar'], shell=False) == ['foo', 'bar']

    def test_format_for_subprocess_list_shell(self):
        assert Platform().format_for_subprocess(['foo', 'bar'], shell=True) == ['foo', 'bar']

    def test_format_for_subprocess_string(self):
        assert Platform().format_for_subprocess('foo bar', shell=False) == 'foo bar'

    def test_format_for_subprocess_string_shell(self):
        assert Platform().format_for_subprocess('foo bar', shell=True) == 'foo bar'

    def test_home(self):
        platform = Platform()

        assert platform.home == platform.home == Path(os.path.expanduser('~'))

    def test_populate_default_popen_kwargs_executable(self):
        platform = Platform()

        kwargs = {}
        platform.populate_default_popen_kwargs(kwargs, shell=True)
        assert not kwargs

        kwargs['executable'] = 'foo'
        platform.populate_default_popen_kwargs(kwargs, shell=True)
        assert kwargs['executable'] == 'foo'


@pytest.mark.requires_macos
class TestMacOS:
    def test_tag(self):
        assert Platform().macos is True

    def test_default_shell(self):
        assert Platform().default_shell == os.environ.get('SHELL', 'bash')

    def test_format_for_subprocess_list(self):
        assert Platform().format_for_subprocess(['foo', 'bar'], shell=False) == ['foo', 'bar']

    def test_format_for_subprocess_list_shell(self):
        assert Platform().format_for_subprocess(['foo', 'bar'], shell=True) == ['foo', 'bar']

    def test_format_for_subprocess_string(self):
        assert Platform().format_for_subprocess('foo bar', shell=False) == ['foo', 'bar']

    def test_format_for_subprocess_string_shell(self):
        assert Platform().format_for_subprocess('foo bar', shell=True) == 'foo bar'

    def test_home(self):
        platform = Platform()

        assert platform.home == platform.home == Path(os.path.expanduser('~'))

    def test_populate_default_popen_kwargs_executable(self, temp_dir):
        new_path = f'{os.environ.get("PATH", "")}{os.pathsep}{temp_dir}'.strip(os.pathsep)
        executable = temp_dir / 'sh'
        executable.touch()
        executable.chmod(executable.stat().st_mode | stat.S_IEXEC)

        kwargs = {}

        platform = Platform()
        with EnvVars({'DYLD_FOO': 'bar', 'PATH': new_path}):
            platform.populate_default_popen_kwargs(kwargs, shell=True)

        assert kwargs['executable'] == str(executable)


@pytest.mark.requires_linux
class TestLinux:
    def test_tag(self):
        assert Platform().linux is True

    def test_default_shell(self):
        assert Platform().default_shell == os.environ.get('SHELL', 'bash')

    def test_format_for_subprocess_list(self):
        assert Platform().format_for_subprocess(['foo', 'bar'], shell=False) == ['foo', 'bar']

    def test_format_for_subprocess_list_shell(self):
        assert Platform().format_for_subprocess(['foo', 'bar'], shell=True) == ['foo', 'bar']

    def test_format_for_subprocess_string(self):
        assert Platform().format_for_subprocess('foo bar', shell=False) == ['foo', 'bar']

    def test_format_for_subprocess_string_shell(self):
        assert Platform().format_for_subprocess('foo bar', shell=True) == 'foo bar'

    def test_home(self):
        platform = Platform()

        assert platform.home == platform.home == Path(os.path.expanduser('~'))

    def test_populate_default_popen_kwargs_executable(self):
        platform = Platform()

        kwargs = {}
        platform.populate_default_popen_kwargs(kwargs, shell=True)
        assert not kwargs

        kwargs['executable'] = 'foo'
        platform.populate_default_popen_kwargs(kwargs, shell=True)
        assert kwargs['executable'] == 'foo'
