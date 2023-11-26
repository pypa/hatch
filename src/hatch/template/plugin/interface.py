class TemplateInterface:
    PLUGIN_NAME = ''
    PRIORITY = 100

    def __init__(self, plugin_config: dict, cache_dir, creation_time):
        self.plugin_config = plugin_config
        self.cache_dir = cache_dir
        self.creation_time = creation_time

    def initialize_config(self, config):
        """
        Allow modification of the configuration passed to every file for new projects
        before the list of files are determined.
        """

    def get_files(self, config):  # noqa: ARG002, PLR6301
        """Add to the list of files for new projects that are written to the file system."""
        return []

    def finalize_files(self, config, files):
        """Allow modification of files for new projects before they are written to the file system."""
