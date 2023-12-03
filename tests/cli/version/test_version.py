import os

import pytest

from hatch.project.core import Project
from hatchling.utils.constants import DEFAULT_BUILD_SCRIPT, DEFAULT_CONFIG_FILE


class TestNoProject:
    def test_random_directory(self, hatch, temp_dir, helpers):
        with temp_dir.as_cwd():
            result = hatch('version')

        assert result.exit_code == 1, result.output
        assert result.output == helpers.dedent(
            """
            No project detected
            """
        )

    def test_configured_project(self, hatch, temp_dir, helpers, config_file):
        project = 'foo'
        config_file.model.mode = 'project'
        config_file.model.project = project
        config_file.model.projects = {project: str(temp_dir)}
        config_file.save()

        with temp_dir.as_cwd():
            result = hatch('version')

        assert result.exit_code == 1, result.output
        assert result.output == helpers.dedent(
            """
            Project foo (not a project)
            """
        )


def test_incompatible_environment(hatch, temp_dir, helpers):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    project = Project(path)
    config = dict(project.raw_config)
    config['build-system']['requires'].append('foo')
    config['tool']['hatch']['metadata'] = {'hooks': {'custom': {}}}
    project.save_config(config)
    helpers.update_project_environment(
        project, 'default', {'skip-install': True, 'python': '9000', **project.config.envs['default']}
    )

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            from hatchling.metadata.plugin.interface import MetadataHookInterface

            class CustomMetadataHook(MetadataHookInterface):
                def update(self, metadata):
                    pass
            """
        )
    )

    with path.as_cwd():
        result = hatch('version')

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Environment `default` is incompatible: cannot locate Python: 9000
        """
    )


def test_show_dynamic(hatch, temp_dir):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        hatch('new', project_name)

    path = temp_dir / 'my-app'

    with path.as_cwd():
        result = hatch('version')

    assert result.exit_code == 0, result.output
    assert result.output == '0.0.1\n'


@pytest.mark.usefixtures('local_backend_process')
def test_show_dynamic_missing_build_dependencies(hatch, helpers, temp_dir):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        hatch('new', project_name)

    path = temp_dir / 'my-app'

    project = Project(path)
    config = dict(project.raw_config)
    config['build-system']['requires'].append('foo')
    project.save_config(config)

    with path.as_cwd():
        result = hatch('version')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Setting up build environment for missing dependencies
        0.0.1
        """
    )


@pytest.mark.usefixtures('local_backend_process')
def test_plugin_dependencies_unmet(hatch, helpers, temp_dir, mock_plugin_installation):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        hatch('new', project_name)

    path = temp_dir / 'my-app'

    dependency = os.urandom(16).hex()
    (path / DEFAULT_CONFIG_FILE).write_text(
        helpers.dedent(
            f"""
            [env]
            requires = ["{dependency}"]
            """
        )
    )

    project = Project(path)
    config = dict(project.raw_config)
    config['build-system']['requires'].append('foo')
    project.save_config(config)

    with path.as_cwd():
        result = hatch('version')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Syncing environment plugin requirements
        Setting up build environment for missing dependencies
        0.0.1
        """
    )
    helpers.assert_plugin_installation(mock_plugin_installation, [dependency])


def test_set_dynamic(hatch, helpers, temp_dir):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        hatch('new', project_name)

    path = temp_dir / 'my-app'

    project = Project(path)
    config = dict(project.raw_config)
    config['tool']['hatch']['metadata'] = {'hooks': {'custom': {}}}
    project.save_config(config)

    build_script = path / DEFAULT_BUILD_SCRIPT
    build_script.write_text(
        helpers.dedent(
            """
            from hatchling.metadata.plugin.interface import MetadataHookInterface

            class CustomMetadataHook(MetadataHookInterface):
                def update(self, metadata):
                    pass
            """
        )
    )

    with path.as_cwd():
        result = hatch('version', 'minor,rc')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Old: 0.0.1
        New: 0.1.0rc0
        """
    )

    with path.as_cwd():
        result = hatch('version')

    assert result.exit_code == 0, result.output
    assert result.output == '0.1.0rc0\n'


def test_show_static(hatch, temp_dir):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        hatch('new', project_name)

    path = temp_dir / 'my-app'

    project = Project(path)
    config = dict(project.raw_config)
    config['project']['version'] = '1.2.3'
    config['project']['dynamic'].remove('version')
    config['tool']['hatch']['metadata'] = {'hooks': {'foo': {}}}
    project.save_config(config)

    with path.as_cwd():
        result = hatch('version')

    assert result.exit_code == 0, result.output
    assert result.output == '1.2.3\n'


def test_set_static(hatch, helpers, temp_dir):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        hatch('new', project_name)

    path = temp_dir / 'my-app'

    project = Project(path)
    config = dict(project.raw_config)
    config['project']['version'] = '1.2.3'
    config['project']['dynamic'].remove('version')
    project.save_config(config)

    with path.as_cwd():
        result = hatch('version', 'minor,rc')

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Cannot set version when it is statically defined by the `project.version` field
        """
    )
