from contextlib import contextmanager

from hatch.utils.fs import Path
from hatch.utils.network import DEFAULT_TIMEOUT, download_file, get_timeout


class TestGetTimeout:
    def test_default(self, monkeypatch):
        monkeypatch.delenv("HATCH_NETWORK_TIMEOUT", raising=False)

        assert get_timeout() == DEFAULT_TIMEOUT

    def test_custom(self, monkeypatch):
        monkeypatch.setenv("HATCH_NETWORK_TIMEOUT", "60")

        assert get_timeout() == 60

    def test_invalid(self, monkeypatch):
        monkeypatch.setenv("HATCH_NETWORK_TIMEOUT", "not-a-number")

        assert get_timeout() == DEFAULT_TIMEOUT


class TestDownloadFile:
    def test_uses_configured_timeout(self, monkeypatch, tmp_path):
        monkeypatch.setenv("HATCH_NETWORK_TIMEOUT", "42")

        captured = {}

        class FakeResponse:
            def iter_bytes(self, chunk_size):  # noqa: ARG002
                yield b"data"

        @contextmanager
        def fake_streaming_response(*args, **kwargs):  # noqa: ARG001
            captured.update(kwargs)
            yield FakeResponse()

        monkeypatch.setattr("hatch.utils.network.streaming_response", fake_streaming_response)

        target = Path(tmp_path, "file.bin")
        download_file(target, "https://example.com/file.bin")

        assert captured["timeout"] == 42
        assert target.read_bytes() == b"data"

    def test_uses_default_timeout(self, monkeypatch, tmp_path):
        monkeypatch.delenv("HATCH_NETWORK_TIMEOUT", raising=False)

        captured = {}

        class FakeResponse:
            def iter_bytes(self, chunk_size):  # noqa: ARG002
                yield b"data"

        @contextmanager
        def fake_streaming_response(*args, **kwargs):  # noqa: ARG001
            captured.update(kwargs)
            yield FakeResponse()

        monkeypatch.setattr("hatch.utils.network.streaming_response", fake_streaming_response)

        target = Path(tmp_path, "file.bin")
        download_file(target, "https://example.com/file.bin")

        assert captured["timeout"] == DEFAULT_TIMEOUT
        assert target.read_bytes() == b"data"
