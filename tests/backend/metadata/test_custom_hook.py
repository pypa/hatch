import re

import pytest

from hatchling.metadata.custom import CustomMetadataHook
from hatchling.utils.constants import DEFAULT_BUILD_SCRIPT


def test_no_path(isolation):
    config = {'path': ''}

    with pytest.raises(ValueError, match='Option `path` for metadata hook `custom` must not be empty if defined'):
        CustomMetadataHook(str(isolation), config)


def test_path_not_string(isolation):
    config = {'path': 3}

    with pytest.raises(TypeError, match='Option `path` for metadata hook `custom` must be a string'):
        CustomMetadataHook(str(isolation), config)


def test_nonexistent(isolation):
    config = {'path': 'test.py'}

    with pytest.raises(OSError, match='Build script does not exist: test.py'):
        CustomMetadataHook(str(isolation), config)


def test_default(temp_dir, helpers):
    config = {}

    file_path = temp_dir / DEFAULT_BUILD_SCRIPT
    file_path.write_text(
        helpers.dedent(
            """
            from hatchling.metadata.plugin.interface import MetadataHookInterface

            class CustomHook(MetadataHookInterface):
                def update(self, metadata):
                    pass

                def foo(self):
                    return self.PLUGIN_NAME, self.root
            """
        )
    )

    with temp_dir.as_cwd():
        hook = CustomMetadataHook(str(temp_dir), config)

    assert hook.foo() == ('custom', str(temp_dir))


def test_explicit_path(temp_dir, helpers):
    config = {'path': f'foo/{DEFAULT_BUILD_SCRIPT}'}

    file_path = temp_dir / 'foo' / DEFAULT_BUILD_SCRIPT
    file_path.ensure_parent_dir_exists()
    file_path.write_text(
        helpers.dedent(
            """
            from hatchling.metadata.plugin.interface import MetadataHookInterface

            class CustomHook(MetadataHookInterface):
                def update(self, metadata):
                    pass

                def foo(self):
                    return self.PLUGIN_NAME, self.root
            """
        )
    )

    with temp_dir.as_cwd():
        hook = CustomMetadataHook(str(temp_dir), config)

    assert hook.foo() == ('custom', str(temp_dir))


def test_no_subclass(temp_dir, helpers):
    config = {'path': f'foo/{DEFAULT_BUILD_SCRIPT}'}

    file_path = temp_dir / 'foo' / DEFAULT_BUILD_SCRIPT
    file_path.ensure_parent_dir_exists()
    file_path.write_text(
        helpers.dedent(
            """
            from hatchling.metadata.plugin.interface import MetadataHookInterface

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
            f'Unable to find a subclass of `MetadataHookInterface` in `foo/{DEFAULT_BUILD_SCRIPT}`: {temp_dir}'
        ),
    ):
        with temp_dir.as_cwd():
            CustomMetadataHook(str(temp_dir), config)
