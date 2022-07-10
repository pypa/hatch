def test_standard(hatch, config_file, helpers):
    result = hatch('config', 'set', 'project', 'foo')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        New setting:
        project = "foo"
        """
    )

    config_file.load()
    assert config_file.model.project == 'foo'


def test_standard_deep(hatch, config_file, helpers):
    result = hatch('config', 'set', 'template.name', 'foo')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        New setting:
        [template]
        name = "foo"
        """
    )

    config_file.load()
    assert config_file.model.template.name == 'foo'


def test_standard_complex_sequence(hatch, config_file, helpers):
    result = hatch('config', 'set', 'dirs.project', "['/foo', '/bar']")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        New setting:
        [dirs]
        project = ["/foo", "/bar"]
        """
    )

    config_file.load()
    assert config_file.model.dirs.project == ['/foo', '/bar']


def test_standard_complex_map(hatch, config_file, helpers):
    result = hatch('config', 'set', 'projects', "{'a': '/foo', 'b': '/bar'}")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        New setting:
        [projects]
        a = "/foo"
        b = "/bar"
        """
    )

    config_file.load()
    assert config_file.model.projects['a'].location == '/foo'
    assert config_file.model.projects['b'].location == '/bar'


def test_standard_hidden(hatch, config_file, helpers):
    result = hatch('config', 'set', 'publish.index.auth', 'foo')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        New setting:
        [publish.index]
        auth = "<...>"
        """
    )

    config_file.load()
    assert config_file.model.publish['index']['auth'] == 'foo'


def test_prompt(hatch, config_file, helpers):
    result = hatch('config', 'set', 'project', input='foo')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Value for `project`: foo
        New setting:
        project = "foo"
        """
    )

    config_file.load()
    assert config_file.model.project == 'foo'


def test_prompt_hidden(hatch, config_file, helpers):
    result = hatch('config', 'set', 'publish.index.auth', input='foo')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Value for `publish.index.auth`:{' '}
        New setting:
        [publish.index]
        auth = "<...>"
        """
    )

    config_file.load()
    assert config_file.model.publish['index']['auth'] == 'foo'


def test_prevent_invalid_config(hatch, config_file, helpers):
    original_mode = config_file.model.mode
    result = hatch('config', 'set', 'mode', 'foo')

    assert result.exit_code == 1
    assert result.output == helpers.dedent(
        """
        Error parsing config:
        mode
          must be one of: aware, local, project
        """
    )

    config_file.load()
    assert config_file.model.mode == original_mode


def test_resolve_project_location_basic(hatch, config_file, helpers, temp_dir):
    config_file.model.project = 'foo'
    config_file.save()

    with temp_dir.as_cwd():
        result = hatch('config', 'set', 'projects.foo', '.')

    path = str(temp_dir).replace('\\', '\\\\')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        New setting:
        [projects]
        foo = "{path}"
        """
    )

    config_file.load()
    assert config_file.model.projects['foo'].location == str(temp_dir)


def test_resolve_project_location_complex(hatch, config_file, helpers, temp_dir):
    config_file.model.project = 'foo'
    config_file.save()

    with temp_dir.as_cwd():
        result = hatch('config', 'set', 'projects.foo.location', '.')

    path = str(temp_dir).replace('\\', '\\\\')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        New setting:
        [projects.foo]
        location = "{path}"
        """
    )

    config_file.load()
    assert config_file.model.projects['foo'].location == str(temp_dir)


def test_project_location_basic_set_first_project(hatch, config_file, helpers, temp_dir):
    with temp_dir.as_cwd():
        result = hatch('config', 'set', 'projects.foo', '.')

    path = str(temp_dir).replace('\\', '\\\\')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        New setting:
        project = "foo"

        [projects]
        foo = "{path}"
        """
    )

    config_file.load()
    assert config_file.model.project == 'foo'
    assert config_file.model.projects['foo'].location == str(temp_dir)


def test_project_location_complex_set_first_project(hatch, config_file, helpers, temp_dir):
    with temp_dir.as_cwd():
        result = hatch('config', 'set', 'projects.foo.location', '.')

    path = str(temp_dir).replace('\\', '\\\\')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        New setting:
        project = "foo"

        [projects.foo]
        location = "{path}"
        """
    )

    config_file.load()
    assert config_file.model.project == 'foo'
    assert config_file.model.projects['foo'].location == str(temp_dir)
