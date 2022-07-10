import pytest

from hatch.publish.plugin.interface import PublisherInterface


class MockPublisher(PublisherInterface):
    PLUGIN_NAME = 'mock'

    def publish(self, artifacts, options):
        pass


class TestDisable:
    def test_default(self, isolation):
        project_config = {}
        plugin_config = {}
        publisher = MockPublisher(None, isolation, None, project_config, plugin_config)

        assert publisher.disable is publisher.disable is False

    def test_project_config(self, isolation):
        project_config = {'disable': True}
        plugin_config = {}
        publisher = MockPublisher(None, isolation, None, project_config, plugin_config)

        assert publisher.disable is True

    def test_project_config_not_boolean(self, isolation):
        project_config = {'disable': 9000}
        plugin_config = {}
        publisher = MockPublisher(None, isolation, None, project_config, plugin_config)

        with pytest.raises(TypeError, match='Field `tool.hatch.publish.mock.disable` must be a boolean'):
            _ = publisher.disable

    def test_plugin_config(self, isolation):
        project_config = {}
        plugin_config = {'disable': True}
        publisher = MockPublisher(None, isolation, None, project_config, plugin_config)

        assert publisher.disable is True

    def test_plugin_config_not_boolean(self, isolation):
        project_config = {}
        plugin_config = {'disable': 9000}
        publisher = MockPublisher(None, isolation, None, project_config, plugin_config)

        with pytest.raises(TypeError, match='Global plugin configuration `publish.mock.disable` must be a boolean'):
            _ = publisher.disable

    def test_project_config_overrides_plugin_config(self, isolation):
        project_config = {'disable': False}
        plugin_config = {'disable': True}
        publisher = MockPublisher(None, isolation, None, project_config, plugin_config)

        assert publisher.disable is False
