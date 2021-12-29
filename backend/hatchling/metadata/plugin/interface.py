class MetadataHookInterface(object):  # no cov
    """
    Example usage:

    === ":octicons-file-code-16: plugin.py"

        ```python
        from hatchling.metadata.plugin.interface import MetadataHookInterface


        class SpecialMetadataHook(MetadataHookInterface):
            PLUGIN_NAME = 'special'
            ...
        ```

    === ":octicons-file-code-16: hooks.py"

        ```python
        from hatchling.plugin import hookimpl

        from .plugin import SpecialMetadataHook


        @hookimpl
        def hatch_register_metadata_hook():
            return SpecialMetadataHook
        ```
    """

    PLUGIN_NAME = ''
    """The name used for selection."""

    def __init__(self, root, config):
        self.__root = root
        self.__config = config

    @property
    def root(self):
        """
        The root of the project tree.
        """
        return self.__root

    @property
    def config(self):
        """
        The hook configuration.

        === ":octicons-file-code-16: pyproject.toml"

            ```toml
            [tool.hatch.metadata.<PLUGIN_NAME>]
            ```

        === ":octicons-file-code-16: hatch.toml"

            ```toml
            [metadata.<PLUGIN_NAME>]
            ```
        """
        return self.__config

    def update(self, metadata):
        """
        :material-align-horizontal-left: **REQUIRED** :material-align-horizontal-right:

        This updates the metadata mapping in-place.
        """
        raise NotImplementedError
