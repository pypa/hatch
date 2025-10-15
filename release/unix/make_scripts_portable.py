from __future__ import annotations

import sys
import sysconfig
from io import BytesIO
from pathlib import Path


def main():
    interpreter = Path(sys.executable).resolve()

    # https://github.com/astral-sh/python-build-standalone/blob/20240415/cpython-unix/build-cpython.sh#L812-L813
    portable_shebang = b'#!/bin/sh\n"exec" "$(dirname $0)/%s" "$0" "$@"\n' % interpreter.name.encode()

    scripts_dir = Path(sysconfig.get_path('scripts'))
    for script in scripts_dir.iterdir():
        if not script.is_file():
            continue

        with script.open('rb') as f:
            data = BytesIO()
            for line in f:
                # Ignore leading blank lines
                if not line.strip():
                    continue

                # Ignore binaries
                if not line.startswith(b'#'):
                    break

                if line.startswith(b'#!%s' % interpreter.parent):
                    executable = Path(line[2:].rstrip().decode()).resolve()
                    data.write(portable_shebang if executable == interpreter else line)
                else:
                    data.write(line)

                data.write(f.read())
                break

        contents = data.getvalue()
        if not contents:
            continue

        with script.open('wb') as f:
            f.write(contents)


if __name__ == '__main__':
    main()
