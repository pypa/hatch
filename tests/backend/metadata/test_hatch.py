import pytest

from hatchling.metadata.core import HatchMetadata
from hatchling.plugin.manager import PluginManager
from hatchling.version.scheme.standard import StandardScheme
from hatchling.version.source.regex import RegexSource


class TestBuildConfig:
    def test_default(self, isolation):
        config = {}
        metadata = HatchMetadata(str(isolation), config, None)

        assert metadata.build_config == metadata.build_config == {}

    def test_not_table(self, isolation):
        config = {'build': 0}
        metadata = HatchMetadata(str(isolation), config, None)

        with pytest.raises(TypeError, match='Field `tool.hatch.build` must be a table'):
            _ = metadata.build_config

    def test_correct(self, isolation):
        config = {'build': {'reproducible': True}}
        metadata = HatchMetadata(str(isolation), config, None)

        assert metadata.build_config == metadata.build_config == {'reproducible': True}


class TestBuildTargets:
    def test_default(self, isolation):
        config = {}
        metadata = HatchMetadata(str(isolation), config, None)

        assert metadata.build_targets == metadata.build_targets == {}

    def test_not_table(self, isolation):
        config = {'build': {'targets': 0}}
        metadata = HatchMetadata(str(isolation), config, None)

        with pytest.raises(TypeError, match='Field `tool.hatch.build.targets` must be a table'):
            _ = metadata.build_targets

    def test_correct(self, isolation):
        config = {'build': {'targets': {'wheel': {'versions': ['standard']}}}}
        metadata = HatchMetadata(str(isolation), config, None)

        assert metadata.build_targets == metadata.build_targets == {'wheel': {'versions': ['standard']}}


class TestVersionSourceName:
    def test_empty(self, isolation):
        with pytest.raises(
            ValueError, match='The `source` option under the `tool.hatch.version` table must not be empty if defined'
        ):
            _ = HatchMetadata(isolation, {'version': {'source': ''}}, None).version.source_name

    def test_not_table(self, isolation):
        with pytest.raises(TypeError, match='Field `tool.hatch.version.source` must be a string'):
            _ = HatchMetadata(isolation, {'version': {'source': 9000}}, None).version.source_name

    def test_correct(self, isolation):
        metadata = HatchMetadata(isolation, {'version': {'source': 'foo'}}, None)

        assert metadata.version.source_name == metadata.version.source_name == 'foo'

    def test_default(self, isolation):
        metadata = HatchMetadata(isolation, {'version': {}}, None)

        assert metadata.version.source_name == metadata.version.source_name == 'regex'


class TestVersionSchemeName:
    def test_missing(self, isolation):
        with pytest.raises(
            ValueError, match='The `scheme` option under the `tool.hatch.version` table must not be empty if defined'
        ):
            _ = HatchMetadata(isolation, {'version': {'scheme': ''}}, None).version.scheme_name

    def test_not_table(self, isolation):
        with pytest.raises(TypeError, match='Field `tool.hatch.version.scheme` must be a string'):
            _ = HatchMetadata(isolation, {'version': {'scheme': 9000}}, None).version.scheme_name

    def test_correct(self, isolation):
        metadata = HatchMetadata(isolation, {'version': {'scheme': 'foo'}}, None)

        assert metadata.version.scheme_name == metadata.version.scheme_name == 'foo'

    def test_default(self, isolation):
        metadata = HatchMetadata(isolation, {'version': {}}, None)

        assert metadata.version.scheme_name == metadata.version.scheme_name == 'standard'


class TestVersionSource:
    def test_unknown(self, isolation):
        with pytest.raises(ValueError, match='Unknown version source: foo'):
            _ = HatchMetadata(isolation, {'version': {'source': 'foo'}}, PluginManager()).version.source

    def test_cached(self, isolation):
        metadata = HatchMetadata(isolation, {'version': {}}, PluginManager())

        assert metadata.version.source is metadata.version.source
        assert isinstance(metadata.version.source, RegexSource)


class TestVersionScheme:
    def test_unknown(self, isolation):
        with pytest.raises(ValueError, match='Unknown version scheme: foo'):
            _ = HatchMetadata(isolation, {'version': {'scheme': 'foo'}}, PluginManager()).version.scheme

    def test_cached(self, isolation):
        metadata = HatchMetadata(isolation, {'version': {}}, PluginManager())

        assert metadata.version.scheme is metadata.version.scheme
        assert isinstance(metadata.version.scheme, StandardScheme)


class TestMetadata:
    def test_default(self, isolation):
        config = {}
        metadata = HatchMetadata(str(isolation), config, None)

        assert metadata.metadata.config == metadata.metadata.config == {}

    def test_not_table(self, isolation):
        config = {'metadata': 0}
        metadata = HatchMetadata(str(isolation), config, None)

        with pytest.raises(TypeError, match='Field `tool.hatch.metadata` must be a table'):
            _ = metadata.metadata.config

    def test_correct(self, isolation):
        config = {'metadata': {'option': True}}
        metadata = HatchMetadata(str(isolation), config, None)

        assert metadata.metadata.config == metadata.metadata.config == {'option': True}


class TestMetadataAllowDirectReferences:
    def test_default(self, isolation):
        config = {}
        metadata = HatchMetadata(str(isolation), config, None)

        assert metadata.metadata.allow_direct_references is metadata.metadata.allow_direct_references is False

    def test_not_boolean(self, isolation):
        config = {'metadata': {'allow-direct-references': 9000}}
        metadata = HatchMetadata(str(isolation), config, None)

        with pytest.raises(TypeError, match='Field `tool.hatch.metadata.allow-direct-references` must be a boolean'):
            _ = metadata.metadata.allow_direct_references

    def test_correct(self, isolation):
        config = {'metadata': {'allow-direct-references': True}}
        metadata = HatchMetadata(str(isolation), config, None)

        assert metadata.metadata.allow_direct_references is True


class TestMetadataAllowAmbiguousFeatures:
    def test_default(self, isolation):
        config = {}
        metadata = HatchMetadata(str(isolation), config, None)

        assert metadata.metadata.allow_ambiguous_features is metadata.metadata.allow_ambiguous_features is False

    def test_not_boolean(self, isolation):
        config = {'metadata': {'allow-ambiguous-features': 9000}}
        metadata = HatchMetadata(str(isolation), config, None)

        with pytest.raises(TypeError, match='Field `tool.hatch.metadata.allow-ambiguous-features` must be a boolean'):
            _ = metadata.metadata.allow_ambiguous_features

    def test_correct(self, isolation):
        config = {'metadata': {'allow-ambiguous-features': True}}
        metadata = HatchMetadata(str(isolation), config, None)

        assert metadata.metadata.allow_ambiguous_features is True
