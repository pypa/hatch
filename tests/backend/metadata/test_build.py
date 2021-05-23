import pytest
from packaging.requirements import Requirement

from hatchling.metadata.core import BuildMetadata


class TestRequires:
    def test_default(self, isolation):
        metadata = BuildMetadata(str(isolation), {})

        assert metadata.requires == metadata.requires == []

    def test_not_array(self, isolation):
        metadata = BuildMetadata(str(isolation), {'requires': 10})

        with pytest.raises(TypeError, match='Field `build-system.requires` must be an array'):
            _ = metadata.requires

    def test_entry_not_string(self, isolation):
        metadata = BuildMetadata(str(isolation), {'requires': [10]})

        with pytest.raises(TypeError, match='Dependency #1 of field `build-system.requires` must be a string'):
            _ = metadata.requires

    def test_invalid_specifier(self, isolation):
        metadata = BuildMetadata(str(isolation), {'requires': ['foo^1']})

        with pytest.raises(ValueError, match='Dependency #1 of field `build-system.requires` is invalid: .+'):
            _ = metadata.requires

    def test_correct(self, isolation):
        metadata = BuildMetadata(str(isolation), {'requires': ['foo', 'bar', 'Baz']})

        assert metadata.requires == metadata.requires == ['foo', 'bar', 'Baz']

    def test_correct_complex_type(self, isolation):
        metadata = BuildMetadata(str(isolation), {'requires': ['foo']})

        assert isinstance(metadata.requires_complex, list)
        assert isinstance(metadata.requires_complex[0], Requirement)


class TestBuildBackend:
    def test_default(self, isolation):
        metadata = BuildMetadata(str(isolation), {})

        assert metadata.build_backend == metadata.build_backend == ''

    def test_not_string(self, isolation):
        metadata = BuildMetadata(str(isolation), {'build-backend': 10})

        with pytest.raises(TypeError, match='Field `build-system.build-backend` must be a string'):
            _ = metadata.build_backend

    def test_correct(self, isolation):
        metadata = BuildMetadata(str(isolation), {'build-backend': 'foo'})

        assert metadata.build_backend == metadata.build_backend == 'foo'


class TestBackendPath:
    def test_default(self, isolation):
        metadata = BuildMetadata(str(isolation), {})

        assert metadata.backend_path == metadata.backend_path == []

    def test_not_array(self, isolation):
        metadata = BuildMetadata(str(isolation), {'backend-path': 10})

        with pytest.raises(TypeError, match='Field `build-system.backend-path` must be an array'):
            _ = metadata.backend_path

    def test_entry_not_string(self, isolation):
        metadata = BuildMetadata(str(isolation), {'backend-path': [10]})

        with pytest.raises(TypeError, match='Entry #1 of field `build-system.backend-path` must be a string'):
            _ = metadata.backend_path

    def test_correct(self, isolation):
        metadata = BuildMetadata(str(isolation), {'backend-path': ['foo', 'bar', 'Baz']})

        assert metadata.backend_path == metadata.backend_path == ['foo', 'bar', 'Baz']
