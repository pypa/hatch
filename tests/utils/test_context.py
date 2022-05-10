import os

import pytest

from hatch.utils.context import Context
from hatch.utils.structures import EnvVars


def test_normal(isolation):
    context = Context(isolation)
    assert context.format('foo {0} {key}', 'arg', key='value') == 'foo arg value'


class TestStatic:
    def test_root(self, isolation):
        context = Context(isolation)
        assert context.format('foo {root}') == f'foo {isolation}'

    def test_home(self, isolation):
        context = Context(isolation)
        assert context.format('foo {home}') == f'foo {os.path.expanduser("~")}'

    def test_directory_separator(self, isolation):
        context = Context(isolation)
        assert context.format('foo {/}') == f'foo {os.path.sep}'

    def test_path_separator(self, isolation):
        context = Context(isolation)
        assert context.format('foo {;}') == f'foo {os.pathsep}'


class TestEnvVars:
    def test_set(self, isolation):
        context = Context(isolation)

        with EnvVars({'BAR': 'foobarbaz'}):
            assert context.format('foo {env:BAR}') == 'foo foobarbaz'

    def test_default(self, isolation):
        context = Context(isolation)

        assert context.format('foo {env:BAR:foobarbaz}') == 'foo foobarbaz'

    def test_default_empty_string(self, isolation):
        context = Context(isolation)

        assert context.format('foo {env:BAR:}') == 'foo '

    def test_default_nested_set(self, isolation):
        context = Context(isolation)

        with EnvVars({'BAZ': 'foobarbaz'}):
            assert context.format('foo {env:BAR:{env:BAZ}}') == 'foo foobarbaz'

    def test_default_nested_default(self, isolation):
        context = Context(isolation)

        assert context.format('foo {env:BAR:{env:BAZ:{home}}}') == f'foo {os.path.expanduser("~")}'

    def test_unset_without_default(self, isolation):
        context = Context(isolation)

        with pytest.raises(ValueError, match='Environment variable without default must be set: BAR'):
            context.format('foo {env:BAR}')


class TestArgs:
    def test_undefined(self, isolation):
        context = Context(isolation)

        assert context.format('foo {args}') == 'foo '

    def test_default(self, isolation):
        context = Context(isolation)

        assert context.format('foo {args: -bar > /dev/null}') == 'foo  -bar > /dev/null'

    def test_default_override(self, isolation):
        context = Context(isolation)

        assert context.format('foo {args: -bar > /dev/null}', args='baz') == 'foo baz'
