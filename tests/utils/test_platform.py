import os

import pytest

from hatch.utils.platform import Platform


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
