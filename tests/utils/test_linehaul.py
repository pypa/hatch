import json
import platform

import pytest

from hatch._version import __version__
from hatch.utils.linehaul import get_linehaul_component, get_linehaul_data


class TestGetLinehaulData:
    def test_installer_info(self):
        data = get_linehaul_data()

        assert data["installer"]["name"] == "hatch"
        assert data["installer"]["version"] == __version__

    def test_python_version(self):
        data = get_linehaul_data()

        assert data["python"] == platform.python_version()

    def test_implementation_info(self):
        data = get_linehaul_data()

        assert data["implementation"]["name"] == platform.python_implementation()
        assert "version" in data["implementation"]

    def test_system_info(self):
        data = get_linehaul_data()

        assert data["system"]["name"] == platform.system()
        assert data["system"]["release"] == platform.release()

    def test_cpu(self):
        data = get_linehaul_data()

        assert data["cpu"] == platform.machine()

    def test_openssl_version_present(self):
        data = get_linehaul_data()

        # ssl module should be available in standard CPython
        assert "openssl_version" in data
        assert data["openssl_version"].startswith(("OpenSSL", "LibreSSL"))


class TestCIDetection:
    _CI_VARS = ("BUILD_BUILDID", "BUILD_ID", "CI", "GITHUB_ACTIONS", "GITLAB_CI", "PIP_IS_CI", "TRAVIS")

    def _clear_ci_env(self, monkeypatch):
        for var in self._CI_VARS:
            monkeypatch.delenv(var, raising=False)

    def test_ci_true_when_env_var_set(self, monkeypatch):
        self._clear_ci_env(monkeypatch)
        monkeypatch.setenv("CI", "true")

        data = get_linehaul_data()

        assert data["ci"] is True

    def test_ci_true_when_env_var_has_any_value(self, monkeypatch):
        self._clear_ci_env(monkeypatch)
        monkeypatch.setenv("BUILD_BUILDID", "12345")

        data = get_linehaul_data()

        assert data["ci"] is True

    def test_ci_none_when_no_env_vars(self, monkeypatch):
        self._clear_ci_env(monkeypatch)

        data = get_linehaul_data()

        assert data["ci"] is None

    @pytest.mark.parametrize(
        "env_var",
        [
            "BUILD_BUILDID",
            "BUILD_ID",
            "CI",
            "GITHUB_ACTIONS",
            "GITLAB_CI",
            "PIP_IS_CI",
            "TRAVIS",
        ],
    )
    def test_each_ci_env_var_detected(self, monkeypatch, env_var):
        self._clear_ci_env(monkeypatch)
        monkeypatch.setenv(env_var, "1")

        data = get_linehaul_data()

        assert data["ci"] is True


class TestDistro:
    def test_macos_distro(self, mocker):
        mocker.patch("hatch.utils.linehaul.sys.platform", "darwin")
        mocker.patch("hatch.utils.linehaul.platform.mac_ver", return_value=("14.0", "", "arm64"))

        data = get_linehaul_data()

        assert data["distro"]["name"] == "macOS"
        assert data["distro"]["version"] == "14.0"

    def test_macos_no_distro_when_mac_ver_empty(self, mocker):
        mocker.patch("hatch.utils.linehaul.sys.platform", "darwin")
        mocker.patch("hatch.utils.linehaul.platform.mac_ver", return_value=("", ("", "", ""), ""))

        data = get_linehaul_data()

        assert "distro" not in data

    def test_no_distro_on_windows(self, mocker):
        mocker.patch("hatch.utils.linehaul.sys.platform", "win32")

        data = get_linehaul_data()

        assert "distro" not in data

    @pytest.mark.requires_linux
    def test_linux_distro(self):
        data = get_linehaul_data()

        # On actual Linux, distro info should be present if distro name is non-empty
        import distro

        if distro.name():
            assert "distro" in data
            assert data["distro"]["name"] == distro.name()


class TestGetLinehaulComponent:
    def test_returns_valid_json(self):
        component = get_linehaul_component()

        data = json.loads(component)
        assert isinstance(data, dict)

    def test_compact_json_format(self):
        component = get_linehaul_component()

        # Compact JSON should have no spaces after separators
        assert ": " not in component
        assert ", " not in component

    def test_keys_are_sorted(self):
        component = get_linehaul_component()

        data = json.loads(component)
        keys = list(data.keys())
        assert keys == sorted(keys)

    def test_contains_required_fields(self):
        component = get_linehaul_component()

        data = json.loads(component)
        assert "installer" in data
        assert "python" in data
        assert "implementation" in data
        assert "system" in data
        assert "cpu" in data
        assert "ci" in data
