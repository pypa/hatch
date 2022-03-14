import pytest

from hatchling.metadata.core import HatchMetadata


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
