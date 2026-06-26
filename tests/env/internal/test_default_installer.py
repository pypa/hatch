from __future__ import annotations

import os
import shutil

import pytest

from hatch.env.internal import (
    build,
    default_installer,
    get_internal_env_config,
    static_analysis,
    test,
    type_check,
    uv,
    uv_available,
)

# Every internal environment config that resolves an installer, paired with the
# config-producing callable. The ``hatch-uv`` environment is included because it
# must also fall back to ``pip`` so that ``uv`` can be bootstrapped on a machine
# where it is not yet available.
INSTALLER_CONFIG_FACTORIES = [
    pytest.param(build.get_default_config, id="hatch-build"),
    pytest.param(static_analysis.get_default_config, id="hatch-static-analysis"),
    pytest.param(static_analysis.get_check_code_config, id="hatch-check-code"),
    pytest.param(static_analysis.get_check_fmt_config, id="hatch-check-fmt"),
    pytest.param(type_check.get_default_config, id="hatch-check-types"),
    pytest.param(test.get_default_config, id="hatch-test"),
    pytest.param(uv.get_default_config, id="hatch-uv"),
]


@pytest.fixture(autouse=True)
def _clear_uv_available_cache():
    # ``uv_available`` is cached so the per-build ``PATH`` scan only runs once. Each test toggles
    # ``uv`` availability, so clear the cache before and after to keep results independent.
    uv_available.cache_clear()
    yield
    uv_available.cache_clear()


def mock_uv(mocker, *, available):
    """Mirror ``VirtualEnvironment.uv_path``'s standalone detection in tests.

    ``uv_available`` augments ``PATH`` with the interpreter's scripts directory and then calls
    ``shutil.which("uv", path=...)``. Patch that lookup directly so the test does not depend on
    whether ``uv`` happens to be installed in the test environment.
    """

    return mocker.patch(
        "hatch.env.internal.shutil.which",
        return_value="/usr/bin/uv" if available else None,
    )


class TestUvAvailableDetection:
    def test_augments_path_with_scripts_dir(self, mocker, tmp_path):
        # Mirror the scripts-dir augmentation used by ``VirtualEnvironment.uv_path``: the scripts
        # directory must be prepended to ``PATH`` before the lookup.
        scripts_dir = str(tmp_path)
        mocker.patch("hatch.env.internal.sysconfig.get_path", return_value=scripts_dir)
        which = mocker.patch("hatch.env.internal.shutil.which", return_value=f"{scripts_dir}/uv")
        mocker.patch.dict(os.environ, {"PATH": "/usr/bin"})

        assert uv_available() is True

        which.assert_called_once_with("uv", path=f"{scripts_dir}{os.pathsep}/usr/bin")

    def test_detects_uv_in_scripts_dir_not_on_bare_path(self, mocker, tmp_path):
        # The exact scenario from the review: ``uv`` is installed as a package and lives in the
        # scripts directory, but that directory is not on the running process's ``PATH``. A bare
        # ``shutil.which("uv")`` would miss it; the augmented lookup must find it.
        scripts_dir = tmp_path
        uv_name = "uv.exe" if os.name == "nt" else "uv"
        uv_binary = scripts_dir / uv_name
        uv_binary.write_text("")
        uv_binary.chmod(0o755)

        mocker.patch("hatch.env.internal.sysconfig.get_path", return_value=str(scripts_dir))
        # Bare PATH does not contain the scripts dir, so unaugmented detection fails...
        mocker.patch.dict(os.environ, {"PATH": str(tmp_path / "nowhere")})
        assert shutil.which("uv") is None

        # ...but ``uv_available`` augments PATH with the scripts dir and therefore finds it.
        assert uv_available() is True

    def test_returns_false_when_uv_missing(self, mocker, tmp_path):
        mocker.patch("hatch.env.internal.sysconfig.get_path", return_value=str(tmp_path))
        mocker.patch("hatch.env.internal.shutil.which", return_value=None)

        assert uv_available() is False

    def test_result_is_cached_across_calls(self, mocker, tmp_path):
        mocker.patch("hatch.env.internal.sysconfig.get_path", return_value=str(tmp_path))
        which = mocker.patch("hatch.env.internal.shutil.which", return_value="/usr/bin/uv")

        assert uv_available() is True
        assert uv_available() is True
        # A single PATH scan, even though ``default_installer`` is invoked for every config build.
        which.assert_called_once()


class TestDefaultInstaller:
    def test_uv_available(self, mocker):
        mock_uv(mocker, available=True)
        assert default_installer() == "uv"

    def test_uv_unavailable(self, mocker):
        mock_uv(mocker, available=False)
        assert default_installer() == "pip"


@pytest.mark.parametrize("get_config", INSTALLER_CONFIG_FACTORIES)
class TestInternalEnvInstallerFallback:
    def test_installer_is_uv_when_uv_available(self, get_config, mocker):
        mock_uv(mocker, available=True)
        assert get_config()["installer"] == "uv"

    def test_installer_is_pip_when_uv_unavailable(self, get_config, mocker):
        mock_uv(mocker, available=False)
        assert get_config()["installer"] == "pip"


class TestInternalEnvConfigFallback:
    def test_all_internal_envs_resolve_pip_without_uv(self, mocker):
        mock_uv(mocker, available=False)
        internal_config = get_internal_env_config()
        for env_name, env_config in internal_config.items():
            if "installer" in env_config:
                assert env_config["installer"] == "pip", env_name

    def test_all_internal_envs_resolve_uv_with_uv(self, mocker):
        mock_uv(mocker, available=True)
        internal_config = get_internal_env_config()
        for env_name, env_config in internal_config.items():
            if "installer" in env_config:
                assert env_config["installer"] == "uv", env_name
