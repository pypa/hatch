import os

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
        result = hatch('dep', 'show', 'requirements')

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Environment `default` is incompatible: cannot locate Python: 9000
        """
    )


def test_project_only(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'

    project = Project(project_path)
    config = dict(project.raw_config)
    config['project']['dependencies'] = ['foo-bar-baz']
    project.save_config(config)

    with project_path.as_cwd():
        result = hatch('dep', 'show', 'requirements', '-p')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        foo-bar-baz
        """
    )


def test_environment_only(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'

    project = Project(project_path)
    helpers.update_project_environment(project, 'default', {'dependencies': ['foo-bar-baz']})

    with project_path.as_cwd():
        result = hatch('dep', 'show', 'requirements', '-e')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        foo-bar-baz
        """
    )


def test_default_both(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'

    project = Project(project_path)
    config = dict(project.raw_config)
    config['project']['dependencies'] = ['foo-bar-baz']
    config['project']['optional-dependencies'] = {
        'feature1': ['bar-baz-foo'],
        'feature2': ['bar-foo-baz'],
        'feature3': ['foo-baz-bar'],
    }
    project.save_config(config)
    helpers.update_project_environment(project, 'default', {'dependencies': ['baz-bar-foo']})

    with project_path.as_cwd():
        result = hatch('dep', 'show', 'requirements')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        baz-bar-foo
        foo-bar-baz
        """
    )


def test_unknown_feature(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'

    with project_path.as_cwd():
        result = hatch('dep', 'show', 'requirements', '-f', 'foo')

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Feature `foo` is not defined in field `project.optional-dependencies`
        """
    )


def test_features_only(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'

    project = Project(project_path)
    config = dict(project.raw_config)
    config['project']['dependencies'] = ['foo-bar-baz']
    config['project']['optional-dependencies'] = {
        'feature1': ['bar-baz-foo'],
        'feature2': ['bar-foo-baz'],
        'feature3': ['foo-baz-bar'],
        'feature4': ['baz-foo-bar'],
    }
    project.save_config(config)
    helpers.update_project_environment(project, 'default', {'dependencies': ['baz-bar-foo']})

    with project_path.as_cwd():
        result = hatch('dep', 'show', 'requirements', '-f', 'feature2', '-f', 'feature1')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        bar-baz-foo
        bar-foo-baz
        """
    )


def test_include_features(hatch, helpers, temp_dir, config_file):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir / 'my-app'

    project = Project(project_path)
    config = dict(project.raw_config)
    config['project']['dependencies'] = ['foo-bar-baz']
    config['project']['optional-dependencies'] = {
        'feature1': ['bar-baz-foo'],
        'feature2': ['bar-foo-baz'],
        'feature3': ['foo-baz-bar'],
        'feature4': ['baz-foo-bar'],
    }
    project.save_config(config)
    helpers.update_project_environment(project, 'default', {'dependencies': ['baz-bar-foo']})

    with project_path.as_cwd():
        result = hatch('dep', 'show', 'requirements', '--all')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        bar-baz-foo
        bar-foo-baz
        baz-bar-foo
        baz-foo-bar
        foo-bar-baz
        foo-baz-bar
        """
    )


def test_plugin_dependencies_unmet(hatch, helpers, temp_dir, config_file, mock_plugin_installation):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

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
    config['project']['dependencies'] = ['foo-bar-baz']
    project.save_config(config)

    with project_path.as_cwd():
        result = hatch('dep', 'show', 'requirements', '-p')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Syncing environment plugin requirements
        foo-bar-baz
        """
    )
    helpers.assert_plugin_installation(mock_plugin_installation, [dependency])
