from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from hatch.env.lockers.uv import UvLocker


@pytest.mark.parametrize(
    ("configured", "expected"),
    [
        pytest.param("3.14t", "3.14", id="freethreaded"),
        pytest.param("3.12", "3.12", id="plain"),
        pytest.param("pypy3.10", "pypy3.10", id="pypy"),
    ],
)
def test_compile_strips_build_variant_from_python_version(tmp_path, configured, expected):
    """uv's --python-version rejects the build variant suffix."""
    environment = MagicMock()
    environment.root = tmp_path
    environment.uv_path = "uv"
    environment.verbosity = 0
    environment.config = {"python": configured}
    environment.get_source_install_args.return_value = []

    UvLocker._compile(  # noqa: SLF001
        environment,
        tmp_path / "requirements.txt",
        upgrade=False,
        upgrade_packages=(),
        layered=False,
        lock_extras=(),
        lock_groups=(),
        requirements_file=None,
    )

    command = environment.platform.check_command.call_args[0][0]
    assert command[command.index("--python-version") + 1] == expected
