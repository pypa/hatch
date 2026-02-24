from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

RUNNER: dict = {}


def main() -> int:
    project_root: str = RUNNER["project_root"]
    output_dir: str = RUNNER["output_dir"]
    hook: str = RUNNER["hook"]
    kwargs: dict[str, str] = RUNNER["kwargs"]
    backend: str = RUNNER["backend"]
    backend_path: str = RUNNER["backend_path"]
    hook_caller_script: str = RUNNER["hook_caller_script"]

    with TemporaryDirectory() as d:
        temp_dir = os.path.realpath(d)
        control_dir = os.path.join(temp_dir, "control")
        os.mkdir(control_dir)
        input_file = os.path.join(control_dir, "input.json")
        output_file = os.path.join(control_dir, "output.json")

        env_vars = dict(os.environ)
        env_vars["_PYPROJECT_HOOKS_BUILD_BACKEND"] = backend
        if backend_path:
            env_vars["_PYPROJECT_HOOKS_BACKEND_PATH"] = backend_path

        if "work_dir" in kwargs:
            work_dir = os.path.join(temp_dir, "work")
            os.mkdir(work_dir)
            kwargs[kwargs.pop("work_dir")] = work_dir
        else:
            work_dir = ""

        with open(input_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({"kwargs": kwargs}))

        script_path = os.path.join(temp_dir, "script.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(hook_caller_script)

        process = subprocess.run(
            [sys.executable, script_path, hook, str(control_dir)],
            cwd=project_root,
            env=env_vars,
            check=False,
        )
        if process.returncode:
            return process.returncode

        with open(output_file, encoding="utf-8") as f:
            output = json.loads(f.read())

        if output.get("no_backend", False):
            sys.stderr.write(f"{output['traceback']}\n{output['backend_error']}\n")
            return 1

        if output.get("unsupported", False):
            sys.stderr.write(output["traceback"])
            return 1

        if output.get("hook_missing", False):
            sys.stderr.write(f"Build backend API `{backend}` is missing hook: {output['missing_hook_name']}\n")
            return 1

        shutil.move(output_file, output_dir)
        if work_dir:
            shutil.move(work_dir, output_dir)

    return 0


if __name__ == "__main__":
    code = main()
    sys.stderr.flush()
    os._exit(code)
