import os

import pytest

from hatch.utils.structures import EnvVars
from hatchling.utils.context import Context


def test_normal(isolation):
    context = Context(isolation)
    assert context.format('foo {0} {key}', 'arg', key='value') == 'foo arg value'


class TestStatic:
    def test_directory_separator(self, isolation):
        context = Context(isolation)
        assert context.format('foo {/}') == f'foo {os.sep}'

    def test_path_separator(self, isolation):
        context = Context(isolation)
        assert context.format('foo {;}') == f'foo {os.pathsep}'


class TestRoot:
    def test_default(self, isolation):
        context = Context(isolation)
        assert context.format('foo {root}') == f'foo {isolation}'

    def test_uri(self, isolation, uri_slash_prefix):
        context = Context(isolation)
        normalized_path = str(isolation).replace(os.sep, '/')
        assert context.format('foo {root:uri}') == f'foo file:{uri_slash_prefix}{normalized_path}'

    def test_real(self, isolation):
        context = Context(isolation)
        assert context.format('foo {root:real}') == f'foo {os.path.realpath(isolation)}'

    def test_unknown_modifier(self, isolation):
        context = Context(isolation)

        with pytest.raises(ValueError, match='Unknown path modifier: bar'):
            context.format('foo {root:bar}')


class TestHome:
    def test_default(self, isolation):
        context = Context(isolation)
        assert context.format('foo {home}') == f'foo {os.path.expanduser("~")}'

    def test_uri(self, isolation, uri_slash_prefix):
        context = Context(isolation)
        normalized_path = os.path.expanduser('~').replace(os.sep, '/')
        assert context.format('foo {home:uri}') == f'foo file:{uri_slash_prefix}{normalized_path}'

    def test_real(self, isolation):
        context = Context(isolation)
        assert context.format('foo {home:real}') == f'foo {os.path.realpath(os.path.expanduser("~"))}'

    def test_unknown_modifier(self, isolation):
        context = Context(isolation)

        with pytest.raises(ValueError, match='Unknown path modifier: bar'):
            context.format('foo {home:bar}')


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

    def test_no_selection(self, isolation):
        context = Context(isolation)

        with pytest.raises(ValueError, match='The `env` context formatting field requires a modifier'):
            context.format('foo {env}')

    def test_unset_without_default(self, isolation):
        context = Context(isolation)

        with pytest.raises(ValueError, match='Nonexistent environment variable must set a default: BAR'):
            context.format('foo {env:BAR}')
