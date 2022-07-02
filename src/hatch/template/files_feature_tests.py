from hatch.template import File
from hatch.utils.fs import Path


class TestsPackageRoot(File):
    def __init__(self, template_config: dict, plugin_config: dict):
        super().__init__(Path('tests', '__init__.py'))
