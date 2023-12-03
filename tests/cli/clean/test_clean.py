import os

import pytest

from hatch.project.core import Project
from hatchling.utils.constants import DEFAULT_BUILD_SCRIPT, DEFAULT_CONFIG_FILE

pytestmark = [pytest.mark.usefixtures('local_backend_process')]


def test(hatch, temp_dir, helpers, config_file, mock_plugin_installation):
    config_file.model.template.plugins['default']['src-layout'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            import pathlib

            from hatchling.builders.hooks.plugin.interface import BuildHookInterface

            class CustomHook(BuildHookInterface):
                def clean(self, versions):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').unlink()
                def initialize(self, version, build_data):
                    if self.target_name == 'wheel':
                        pathlib.Path('my_app', 'lib.so').touch()
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config['tool']['hatch']['build'] = {'hooks': {'custom': {'path': build_script.name}}}
    project.save_config(config)

    with path.as_cwd():
        result = hatch('build')
        assert result.exit_code == 0, result.output

    build_directory = path / 'dist'
    assert build_directory.is_dir()
    build_artifact = path / 'my_app' / 'lib.so'
    assert build_artifact.is_file()

    artifacts = list(build_directory.iterdir())
    assert len(artifacts) == 2

    dependency = os.urandom(16).hex()
    (path / DEFAULT_CONFIG_FILE).write_text(
        helpers.dedent(
            f"""
            [env]
            requires = ["{dependency}"]
            """
        )
    )

    with path.as_cwd():
        result = hatch('version', 'minor')
        assert result.exit_code == 0, result.output

        result = hatch('clean')
        assert result.exit_code == 0, result.output

    artifacts = list(build_directory.iterdir())
    assert not artifacts
    assert not build_artifact.exists()

    assert result.output == helpers.dedent(
        """
        Syncing environment plugin requirements
        Setting up build environment
        Setting up build environment
        """
    )
    helpers.assert_plugin_installation(mock_plugin_installation, [dependency])
