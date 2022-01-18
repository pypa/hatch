from hatch.project.core import Project


def test_show_dynamic(hatch, temp_dir):
    project_name = 'My App'

    with temp_dir.as_cwd():
        hatch('new', project_name)

    path = temp_dir / 'my-app'

    with path.as_cwd():
        result = hatch('version')

    assert result.exit_code == 0, result.output
    assert result.output == '0.0.1\n'


def test_set_dynamic(hatch, helpers, temp_dir):
    project_name = 'My App'

    with temp_dir.as_cwd():
        hatch('new', project_name)

    path = temp_dir / 'my-app'

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
    project_name = 'My App'

    with temp_dir.as_cwd():
        hatch('new', project_name)

    path = temp_dir / 'my-app'

    project = Project(path)
    config = dict(project.raw_config)
    config['project']['version'] = '1.2.3'
    project.save_config(config)

    with path.as_cwd():
        result = hatch('version')

    assert result.exit_code == 0, result.output
    assert result.output == '1.2.3\n'


def test_set_static(hatch, helpers, temp_dir):
    project_name = 'My App'

    with temp_dir.as_cwd():
        hatch('new', project_name)

    path = temp_dir / 'my-app'

    project = Project(path)
    config = dict(project.raw_config)
    config['project']['version'] = '1.2.3'
    project.save_config(config)

    with path.as_cwd():
        result = hatch('version', 'minor,rc')

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Cannot set version when it is statically defined by the `project.version` field
        """
    )
