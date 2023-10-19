import os
from hashlib import sha256

from hatch.project.core import Project
from hatchling.utils.constants import DEFAULT_BUILD_SCRIPT, DEFAULT_CONFIG_FILE


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
        result = hatch('dep', 'hash')

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Environment `default` is incompatible: cannot locate Python: 9000
        """
    )


def test_all(hatch, helpers, temp_dir):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'

    project = Project(project_path)
    config = dict(project.raw_config)
    config['project']['dependencies'] = ['Foo', 'bar[ A, b]']
    project.save_config(config)
    helpers.update_project_environment(project, 'default', {'dependencies': ['bAZ >= 0']})
    expected_hash = sha256(b'bar[a,b]baz>=0foo').hexdigest()

    with project_path.as_cwd():
        result = hatch('dep', 'hash')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        {expected_hash}
        """
    )


def test_project_only(hatch, helpers, temp_dir):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'

    project = Project(project_path)
    config = dict(project.raw_config)
    config['project']['dependencies'] = ['Foo', 'bar[ A, b]']
    project.save_config(config)
    helpers.update_project_environment(project, 'default', {'dependencies': ['bAZ >= 0']})
    expected_hash = sha256(b'bar[a,b]foo').hexdigest()

    with project_path.as_cwd():
        result = hatch('dep', 'hash', '-p')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        {expected_hash}
        """
    )


def test_plugin_dependencies_unmet(hatch, helpers, temp_dir, mock_plugin_installation):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'

    dependency = os.urandom(16).hex()
    (project_path / DEFAULT_CONFIG_FILE).write_text(
        helpers.dedent(
            f"""
            [env]
            requires = ["{dependency}"]
            """
        )
    )

    project = Project(project_path)
    config = dict(project.raw_config)
    config['project']['dependencies'] = ['Foo', 'bar[ A, b]']
    project.save_config(config)
    helpers.update_project_environment(project, 'default', {'dependencies': ['bAZ >= 0']})
    expected_hash = sha256(b'bar[a,b]foo').hexdigest()

    with project_path.as_cwd():
        result = hatch('dep', 'hash', '-p')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Syncing environment plugin requirements
        {expected_hash}
        """
    )
    helpers.assert_plugin_installation(mock_plugin_installation, [dependency])
