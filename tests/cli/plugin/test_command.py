import shutil

import importlib_resources


def test_run_command(hatch, temp_dir, helpers):
    project_dir = temp_dir / "cli-plugin"
    shutil.copytree(importlib_resources.files(__package__) / "cli-plugin", project_dir)

    with project_dir.as_cwd():
        result1 = hatch("new", "--init")
        result = hatch("random")

    assert result.exit_code == 0, result.output
    assert result.output == 'random\n'
