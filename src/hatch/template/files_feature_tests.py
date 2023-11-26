from hatch.template import File
from hatch.utils.fs import Path


class TestsPackageRoot(File):
    def __init__(
        self,
        template_config: dict,  # noqa: ARG002
        plugin_config: dict,  # noqa: ARG002
    ):
        super().__init__(Path('tests', '__init__.py'))
