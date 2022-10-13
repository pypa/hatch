from hatchling.builders.plugin.interface import BuilderInterface


class MockBuilder(BuilderInterface):  # no cov
    def get_version_api(self):
        return {}
