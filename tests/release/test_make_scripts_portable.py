import runpy
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest

MAKE_SCRIPTS_PORTABLE = Path(__file__).resolve().parents[2] / "release" / "unix" / "make_scripts_portable.py"
ENTRY_POINT = b"import sys\nprint(sys.argv[1:])\n"


def _portable_shebang(interpreter_name):
    return (b"#!/bin/sh\n'''exec' \"$(dirname -- \"$0\")/%s\" \"$0\" \"$@\"\n' '''\n") % interpreter_name.encode()


def _resolved_interpreter():
    return Path(sys.executable).resolve()


def _rewrite_scripts(monkeypatch, scripts_dir):
    interpreter = _resolved_interpreter()
    symlink = scripts_dir / interpreter.name
    if not symlink.is_symlink():
        symlink.symlink_to(interpreter)

    monkeypatch.setattr(sys, "executable", str(symlink))
    original_get_path = sysconfig.get_path

    def get_path(name, *args, **kwargs):
        if name == "scripts":
            return str(scripts_dir)
        return original_get_path(name, *args, **kwargs)

    monkeypatch.setattr(sysconfig, "get_path", get_path)
    runpy.run_path(str(MAKE_SCRIPTS_PORTABLE), run_name="__main__")


def _write_script(directory, name, body):
    script = directory / name
    script.write_bytes(b"#!" + str(_resolved_interpreter()).encode() + b"\n" + body)
    script.chmod(0o755)
    return script


def _run_script(script, *args):
    return subprocess.run([str(script), *args], check=False, capture_output=True)


@pytest.mark.requires_unix
class TestMakeScriptsPortable:
    def test_path_with_spaces(self, tmp_path, monkeypatch):
        bin_dir = tmp_path / "Application Support" / "pyapp" / "python" / "bin"
        bin_dir.mkdir(parents=True)
        script = _write_script(bin_dir, "hatch", ENTRY_POINT)

        _rewrite_scripts(monkeypatch, bin_dir)

        assert script.read_bytes().startswith(_portable_shebang(_resolved_interpreter().name))
        result = _run_script(script, "foo", "bar baz")
        assert result.returncode == 0, result.stderr
        assert result.stdout == b"['foo', 'bar baz']\n"

    def test_path_without_spaces(self, tmp_path, monkeypatch):
        bin_dir = tmp_path / "python" / "bin"
        bin_dir.mkdir(parents=True)
        script = _write_script(bin_dir, "hatch", ENTRY_POINT)

        _rewrite_scripts(monkeypatch, bin_dir)

        assert script.read_bytes() == _portable_shebang(_resolved_interpreter().name) + ENTRY_POINT
        compile(script.read_bytes(), str(script), "exec")
        result = _run_script(script, "hello world")
        assert result.returncode == 0, result.stderr
        assert result.stdout == b"['hello world']\n"

    def test_leading_hyphen_directory(self, tmp_path, monkeypatch):
        bin_dir = tmp_path / "-dir" / "bin"
        bin_dir.mkdir(parents=True)
        script = _write_script(bin_dir, "hatch", ENTRY_POINT)

        _rewrite_scripts(monkeypatch, bin_dir)

        assert b'dirname -- "$0"' in script.read_bytes()
        result = _run_script(script, "ok")
        assert result.returncode == 0, result.stderr
        assert result.stdout == b"['ok']\n"

    def test_leading_blank_lines(self, tmp_path, monkeypatch):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        interpreter = _resolved_interpreter()
        script = bin_dir / "hatch"
        body = b"print('ok')\n"
        script.write_bytes(b"\n\n#!" + str(interpreter).encode() + b"\n" + body)
        script.chmod(0o755)

        _rewrite_scripts(monkeypatch, bin_dir)

        assert script.read_bytes() == _portable_shebang(interpreter.name) + body

    def test_non_targets_are_unmodified(self, tmp_path, monkeypatch):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        binary = bin_dir / "binary"
        binary.write_bytes(b"\x7fELF\x00\x01")
        plain = bin_dir / "plain"
        plain.write_bytes(b"print('hello')\n")
        other = bin_dir / "other"
        other.write_bytes(b"#!/other/interpreter\nprint('x')\n")
        untouched = {path: path.read_bytes() for path in (binary, plain, other)}

        script = _write_script(bin_dir, "hatch", ENTRY_POINT)
        _rewrite_scripts(monkeypatch, bin_dir)

        for path, contents in untouched.items():
            assert path.read_bytes() == contents

        rewritten = script.read_bytes()
        assert rewritten.startswith(b"#!/bin/sh\n")
        _rewrite_scripts(monkeypatch, bin_dir)
        assert script.read_bytes() == rewritten
