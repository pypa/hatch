from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).parents[2] / "release" / "unix" / "make_scripts_portable.py"


def load_module():
    spec = importlib.util.spec_from_file_location("unix_make_scripts_portable", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_portable_shebang_quotes_script_path(temp_dir, monkeypatch):
    scripts_dir = temp_dir / "Application Support" / "pyapp" / "hatch" / "python" / "bin"
    scripts_dir.mkdir(parents=True)
    interpreter = scripts_dir / "python3.12"
    interpreter.touch()
    script = scripts_dir / "hatch"
    script.write_bytes(b"#!%s\nprint('ok')\n" % str(interpreter).encode())

    module = load_module()
    monkeypatch.setattr(module.sys, "executable", str(interpreter))
    monkeypatch.setattr(
        module.sysconfig,
        "get_path",
        lambda name: str(scripts_dir) if name == "scripts" else None,
    )

    module.main()

    assert script.read_bytes() == (b'#!/bin/sh\n"exec" "$(dirname "$0")/python3.12" "$0" "$@"\nprint(\'ok\')\n')
