import importlib.util
from pathlib import Path


def test_launchers_url_pinned():
    # uv 0.9.9+ trampolines no longer read the appended UVUV trailer
    path = Path(__file__).resolve().parents[2] / "release" / "windows" / "make_scripts_portable.py"
    spec = importlib.util.spec_from_file_location("make_scripts_portable", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.LAUNCHERS_URL == (
        "https://raw.githubusercontent.com/astral-sh/uv/0.9.8/crates/uv-trampoline-builder/trampolines"
    )
