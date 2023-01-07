import re

import pytest

from hatch.env.collectors.custom import CustomEnvironmentCollector
from hatch.plugin.constants import DEFAULT_CUSTOM_SCRIPT


def test_no_path(isolation):
    config = {'path': ''}

    with pytest.raises(
        ValueError, match='Option `path` for environment collector `custom` must not be empty if defined'
    ):
        CustomEnvironmentCollector(str(isolation), config)


def test_path_not_string(isolation):
    config = {'path': 3}

    with pytest.raises(TypeError, match='Option `path` for environment collector `custom` must be a string'):
        CustomEnvironmentCollector(str(isolation), config)


def test_nonexistent(isolation):
    config = {'path': 'test.py'}

    with pytest.raises(OSError, match='Plugin script does not exist: test.py'):
        CustomEnvironmentCollector(str(isolation), config)


def test_default(temp_dir, helpers):
    config = {}

    file_path = temp_dir / DEFAULT_CUSTOM_SCRIPT
    file_path.write_text(
        helpers.dedent(
            """
            from hatch.env.collectors.plugin.interface import EnvironmentCollectorInterface

            class CustomHook(EnvironmentCollectorInterface):
                def foo(self):
                    return self.PLUGIN_NAME, self.root
            """
        )
    )

    with temp_dir.as_cwd():
        hook = CustomEnvironmentCollector(str(temp_dir), config)

    assert hook.foo() == ('custom', str(temp_dir))


def test_explicit_path(temp_dir, helpers):
    config = {'path': f'foo/{DEFAULT_CUSTOM_SCRIPT}'}

    file_path = temp_dir / 'foo' / DEFAULT_CUSTOM_SCRIPT
    file_path.ensure_parent_dir_exists()
    file_path.write_text(
        helpers.dedent(
            """
            from hatch.env.collectors.plugin.interface import EnvironmentCollectorInterface

            class CustomHook(EnvironmentCollectorInterface):
                def foo(self):
                    return self.PLUGIN_NAME, self.root
            """
        )
    )

    with temp_dir.as_cwd():
        hook = CustomEnvironmentCollector(str(temp_dir), config)

    assert hook.foo() == ('custom', str(temp_dir))


def test_no_subclass(temp_dir, helpers):
    config = {'path': f'foo/{DEFAULT_CUSTOM_SCRIPT}'}

    file_path = temp_dir / 'foo' / DEFAULT_CUSTOM_SCRIPT
    file_path.ensure_parent_dir_exists()
    file_path.write_text(
        helpers.dedent(
            """
            from hatch.env.collectors.plugin.interface import EnvironmentCollectorInterface

            foo = None
            bar = 'baz'

            class CustomHook:
                pass
            """
        )
    )

    with pytest.raises(
        ValueError,
        match=re.escape(
            f'Unable to find a subclass of `EnvironmentCollectorInterface` in `foo/{DEFAULT_CUSTOM_SCRIPT}`: {temp_dir}'
        ),
    ), temp_dir.as_cwd():
        CustomEnvironmentCollector(str(temp_dir), config)
