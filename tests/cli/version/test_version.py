def test_show(hatch, temp_dir):
    project_name = 'My App'

    with temp_dir.as_cwd():
        hatch('new', project_name)

    path = temp_dir / 'my-app'

    with path.as_cwd():
        result = hatch('version')

    assert result.exit_code == 0, result.output
    assert result.output == '0.0.1\n'


def test_set(hatch, helpers, temp_dir):
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
        New: 0.1rc0
        """
    )

    with path.as_cwd():
        result = hatch('version')

    assert result.exit_code == 0, result.output
    assert result.output == '0.1rc0\n'
