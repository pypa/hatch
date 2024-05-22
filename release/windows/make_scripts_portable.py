from __future__ import annotations

import sys
import sysconfig
from contextlib import closing
from importlib.metadata import entry_points
from io import BytesIO
from os.path import relpath
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

LAUNCHERS_URL = 'https://raw.githubusercontent.com/astral-sh/uv/main/crates/uv-trampoline/trampolines'
SCRIPT_TEMPLATE = """\
#!{executable}
# -*- coding: utf-8 -*-
import re
import sys
from {module} import {import_name}
if __name__ == "__main__":
    sys.argv[0] = re.sub(r"(-script\\.pyw|\\.exe)?$", "", sys.argv[0])
    sys.exit({function}())
"""


def select_entry_points(ep, group):
    return ep.select(group=group) if sys.version_info[:2] >= (3, 10) else ep.get(group, [])


def fetch_launcher(launcher_name):
    with urlopen(f'{LAUNCHERS_URL}/{launcher_name}') as f:  # noqa: S310
        return f.read()


def main():
    interpreters_dir = Path(sys.executable).parent
    scripts_dir = Path(sysconfig.get_path('scripts'))

    ep = entry_points()
    for group, interpreter_name, launcher_name in (
        ('console_scripts', 'python.exe', 'uv-trampoline-x86_64-console.exe'),
        ('gui_scripts', 'pythonw.exe', 'uv-trampoline-x86_64-gui.exe'),
    ):
        interpreter = interpreters_dir / interpreter_name
        relative_interpreter_path = relpath(interpreter, scripts_dir)
        launcher_data = fetch_launcher(launcher_name)

        for script in select_entry_points(ep, group):
            # https://github.com/astral-sh/uv/tree/main/crates/uv-trampoline#how-do-you-use-it
            with closing(BytesIO()) as buf:
                # Launcher
                buf.write(launcher_data)

                # Zipped script
                with TemporaryDirectory() as td:
                    zip_path = Path(td) / 'script.zip'
                    with ZipFile(zip_path, 'w') as zf:
                        # Ensure reproducibility
                        zip_info = ZipInfo('__main__.py', (2020, 2, 2, 0, 0, 0))
                        zip_info.external_attr = (0o644 & 0xFFFF) << 16

                        module, _, attrs = script.value.partition(':')
                        contents = SCRIPT_TEMPLATE.format(
                            executable=relative_interpreter_path,
                            module=module,
                            import_name=attrs.split('.')[0],
                            function=attrs,
                        )
                        zf.writestr(zip_info, contents, compress_type=ZIP_DEFLATED)

                    buf.write(zip_path.read_bytes())

                # Interpreter path
                interpreter_path = relative_interpreter_path.encode('utf-8')
                buf.write(interpreter_path)

                # Interpreter path length
                interpreter_path_length = len(interpreter_path).to_bytes(4, 'little')
                buf.write(interpreter_path_length)

                # Magic number
                buf.write(b'UVUV')

                script_data = buf.getvalue()

            script_path = scripts_dir / f'{script.name}.exe'
            script_path.write_bytes(script_data)


if __name__ == '__main__':
    main()
