import pytest

from hatch.config.constants import ConfigEnvVars


def remove_trailing_spaces(text):
    return ''.join(f'{line.rstrip()}\n' for line in text.splitlines(True))


class TestErrors:
    def test_path_is_file(self, hatch, temp_dir):
        with temp_dir.as_cwd():
            path = temp_dir / 'foo'
            path.touch()

            result = hatch('new', 'foo')

        assert result.exit_code == 1
        assert result.output == f'Path `{path}` points to a file.\n'

    def test_path_not_empty(self, hatch, temp_dir):
        with temp_dir.as_cwd():
            path = temp_dir / 'foo'
            (path / 'bar').ensure_dir_exists()

            result = hatch('new', 'foo')

        assert result.exit_code == 1
        assert result.output == f'Directory `{path}` is not empty.\n'

    def test_no_plugins_found(self, hatch, config_file, temp_dir):
        project_name = 'My.App'
        config_file.model.template.plugins = {'foo': {}}
        config_file.save()

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 1
        assert result.output == 'None of the defined plugins were found: foo\n'

    def test_some_not_plugins_found(self, hatch, config_file, temp_dir):
        project_name = 'My.App'
        config_file.model.template.plugins['foo'] = {}
        config_file.save()

        with temp_dir.as_cwd():
            result = hatch('new', project_name)

        assert result.exit_code == 1
        assert result.output == 'Some of the defined plugins were not found: foo\n'


def test_default(hatch, helpers, temp_dir):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    path = temp_dir / 'my-app'

    expected_files = helpers.get_template_files('new.default', project_name)
    helpers.assert_files(path, expected_files, check_contents=True)

    assert result.exit_code == 0, result.output
    assert remove_trailing_spaces(result.output) == helpers.dedent(
        """
        my-app
        ├── my_app
        │   ├── __about__.py
        │   └── __init__.py
        ├── tests
        │   └── __init__.py
        ├── LICENSE.txt
        ├── README.md
        └── pyproject.toml
        """
    )


def test_default_explicit_path(hatch, helpers, temp_dir):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name, '.')

    expected_files = helpers.get_template_files('new.default', project_name)
    helpers.assert_files(temp_dir, expected_files, check_contents=True)

    assert result.exit_code == 0, result.output
    assert remove_trailing_spaces(result.output) == helpers.dedent(
        """
        my_app
        ├── __about__.py
        └── __init__.py
        tests
        └── __init__.py
        LICENSE.txt
        README.md
        pyproject.toml
        """
    )


def test_default_empty_plugins_table(hatch, helpers, config_file, temp_dir):
    project_name = 'My.App'
    config_file.model.template.plugins = {}
    config_file.save()

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    path = temp_dir / 'my-app'

    expected_files = helpers.get_template_files('new.default', project_name)
    helpers.assert_files(path, expected_files, check_contents=True)

    assert result.exit_code == 0, result.output
    assert remove_trailing_spaces(result.output) == helpers.dedent(
        """
        my-app
        ├── my_app
        │   ├── __about__.py
        │   └── __init__.py
        ├── tests
        │   └── __init__.py
        ├── LICENSE.txt
        ├── README.md
        └── pyproject.toml
        """
    )


@pytest.mark.requires_internet
def test_default_no_license_cache(hatch, helpers, temp_dir):
    project_name = 'My.App'
    cache_dir = temp_dir / 'cache'
    cache_dir.mkdir()

    with temp_dir.as_cwd({ConfigEnvVars.CACHE: str(cache_dir)}):
        result = hatch('new', project_name)

    path = temp_dir / 'my-app'

    expected_files = helpers.get_template_files('new.default', project_name)
    helpers.assert_files(path, expected_files, check_contents=True)

    assert result.exit_code == 0, result.output
    assert remove_trailing_spaces(result.output) == helpers.dedent(
        """
        my-app
        ├── my_app
        │   ├── __about__.py
        │   └── __init__.py
        ├── tests
        │   └── __init__.py
        ├── LICENSE.txt
        ├── README.md
        └── pyproject.toml
        """
    )


def test_licenses_multiple(hatch, helpers, config_file, temp_dir):
    project_name = 'My.App'
    config_file.model.template.licenses.default = ['MIT', 'Apache-2.0']
    config_file.save()

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    path = temp_dir / 'my-app'

    expected_files = helpers.get_template_files('new.licenses_multiple', project_name)
    helpers.assert_files(path, expected_files, check_contents=True)

    assert result.exit_code == 0, result.output
    assert remove_trailing_spaces(result.output) == helpers.dedent(
        """
        my-app
        ├── LICENSES
        │   ├── Apache-2.0.txt
        │   └── MIT.txt
        ├── my_app
        │   ├── __about__.py
        │   └── __init__.py
        ├── tests
        │   └── __init__.py
        ├── README.md
        └── pyproject.toml
        """
    )


def test_licenses_empty(hatch, helpers, config_file, temp_dir):
    project_name = 'My.App'
    config_file.model.template.licenses.default = []
    config_file.save()

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    path = temp_dir / 'my-app'

    expected_files = helpers.get_template_files('new.licenses_empty', project_name)
    helpers.assert_files(path, expected_files, check_contents=True)

    assert result.exit_code == 0, result.output
    assert remove_trailing_spaces(result.output) == helpers.dedent(
        """
        my-app
        ├── my_app
        │   ├── __about__.py
        │   └── __init__.py
        ├── tests
        │   └── __init__.py
        ├── README.md
        └── pyproject.toml
        """
    )


def test_projects_urls_space_in_label(hatch, helpers, config_file, temp_dir):
    project_name = 'My.App'
    config_file.model.template.plugins['default']['project_urls'] = {
        'Documentation': 'https://github.com/unknown/{project_name_normalized}#readme',
        'Source': 'https://github.com/unknown/{project_name_normalized}',
        'Bug Tracker': 'https://github.com/unknown/{project_name_normalized}/issues',
    }
    config_file.save()

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    path = temp_dir / 'my-app'

    expected_files = helpers.get_template_files('new.projects_urls_space_in_label', project_name)
    helpers.assert_files(path, expected_files, check_contents=True)

    assert result.exit_code == 0, result.output
    assert remove_trailing_spaces(result.output) == helpers.dedent(
        """
        my-app
        ├── my_app
        │   ├── __about__.py
        │   └── __init__.py
        ├── tests
        │   └── __init__.py
        ├── LICENSE.txt
        ├── README.md
        └── pyproject.toml
        """
    )


def test_projects_urls_empty(hatch, helpers, config_file, temp_dir):
    project_name = 'My.App'
    config_file.model.template.plugins['default']['project_urls'] = {}
    config_file.save()

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    path = temp_dir / 'my-app'

    expected_files = helpers.get_template_files('new.projects_urls_empty', project_name)
    helpers.assert_files(path, expected_files, check_contents=True)

    assert result.exit_code == 0, result.output
    assert remove_trailing_spaces(result.output) == helpers.dedent(
        """
        my-app
        ├── my_app
        │   ├── __about__.py
        │   └── __init__.py
        ├── tests
        │   └── __init__.py
        ├── LICENSE.txt
        ├── README.md
        └── pyproject.toml
        """
    )


def test_feature_cli(hatch, helpers, temp_dir):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name, '--cli')

    path = temp_dir / 'my-app'

    expected_files = helpers.get_template_files('new.feature_cli', project_name)
    helpers.assert_files(path, expected_files, check_contents=True)

    assert result.exit_code == 0, result.output
    assert remove_trailing_spaces(result.output) == helpers.dedent(
        """
        my-app
        ├── my_app
        │   ├── cli
        │   │   └── __init__.py
        │   ├── __about__.py
        │   ├── __init__.py
        │   └── __main__.py
        ├── tests
        │   └── __init__.py
        ├── LICENSE.txt
        ├── README.md
        └── pyproject.toml
        """
    )


def test_feature_ci(hatch, helpers, config_file, temp_dir):
    config_file.model.template.plugins['default']['ci'] = True
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    path = temp_dir / 'my-app'

    expected_files = helpers.get_template_files('new.feature_ci', project_name)
    helpers.assert_files(path, expected_files, check_contents=True)

    assert result.exit_code == 0, result.output
    assert remove_trailing_spaces(result.output) == helpers.dedent(
        """
        my-app
        ├── .github
        │   └── workflows
        │       └── test.yml
        ├── my_app
        │   ├── __about__.py
        │   └── __init__.py
        ├── tests
        │   └── __init__.py
        ├── LICENSE.txt
        ├── README.md
        └── pyproject.toml
        """
    )


def test_feature_src_layout(hatch, helpers, config_file, temp_dir):
    config_file.model.template.plugins['default']['src-layout'] = True
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    path = temp_dir / 'my-app'

    expected_files = helpers.get_template_files('new.feature_src_layout', project_name)
    helpers.assert_files(path, expected_files, check_contents=True)

    assert result.exit_code == 0, result.output
    assert remove_trailing_spaces(result.output) == helpers.dedent(
        """
        my-app
        ├── src
        │   └── my_app
        │       ├── __about__.py
        │       └── __init__.py
        ├── tests
        │   └── __init__.py
        ├── LICENSE.txt
        ├── README.md
        └── pyproject.toml
        """
    )


def test_feature_tests_disable(hatch, helpers, config_file, temp_dir):
    config_file.model.template.plugins['default']['tests'] = False
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)

    path = temp_dir / 'my-app'

    expected_files = helpers.get_template_files('new.basic', project_name)
    helpers.assert_files(path, expected_files, check_contents=True)

    assert result.exit_code == 0, result.output
    assert remove_trailing_spaces(result.output) == helpers.dedent(
        """
        my-app
        ├── my_app
        │   ├── __about__.py
        │   └── __init__.py
        ├── LICENSE.txt
        ├── README.md
        └── pyproject.toml
        """
    )


def test_no_project_name_error(hatch, helpers, temp_dir):
    with temp_dir.as_cwd():
        result = hatch('new')

    assert result.exit_code == 1
    assert remove_trailing_spaces(result.output) == helpers.dedent(
        """
        Missing required argument for the project name, use the -i/--interactive flag.
        """
    )


def test_interactive(hatch, helpers, temp_dir):
    project_name = 'My.App'
    description = 'foo \u2764'

    with temp_dir.as_cwd():
        result = hatch('new', '-i', input=f'{project_name}\n{description}')

    path = temp_dir / 'my-app'

    expected_files = helpers.get_template_files('new.default', project_name, description=description)
    helpers.assert_files(path, expected_files, check_contents=True)

    assert result.exit_code == 0, result.output
    assert remove_trailing_spaces(result.output) == helpers.dedent(
        f"""
        Project name: {project_name}
        Description []: {description}

        my-app
        ├── my_app
        │   ├── __about__.py
        │   └── __init__.py
        ├── tests
        │   └── __init__.py
        ├── LICENSE.txt
        ├── README.md
        └── pyproject.toml
        """
    )


def test_no_project_name_enables_interactive(hatch, helpers, temp_dir):
    project_name = 'My.App'
    description = 'foo'

    with temp_dir.as_cwd():
        result = hatch('new', '-i', input=f'{project_name}\n{description}')

    path = temp_dir / 'my-app'

    expected_files = helpers.get_template_files('new.default', project_name, description=description)
    helpers.assert_files(path, expected_files, check_contents=True)

    assert result.exit_code == 0, result.output
    assert remove_trailing_spaces(result.output) == helpers.dedent(
        f"""
        Project name: {project_name}
        Description []: {description}

        my-app
        ├── my_app
        │   ├── __about__.py
        │   └── __init__.py
        ├── tests
        │   └── __init__.py
        ├── LICENSE.txt
        ├── README.md
        └── pyproject.toml
        """
    )


def test_initialize_fresh(hatch, helpers, temp_dir):
    project_name = 'My.App'
    description = 'foo'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    project_file = path / 'pyproject.toml'
    project_file.remove()
    assert not project_file.is_file()

    with path.as_cwd():
        result = hatch('new', '--init', input=f'{project_name}\n{description}')

    expected_files = helpers.get_template_files('new.default', project_name, description=description)
    helpers.assert_files(path, expected_files, check_contents=True)

    assert result.exit_code == 0, result.output
    assert remove_trailing_spaces(result.output) == helpers.dedent(
        f"""
        Project name: {project_name}
        Description []: {description}

        Wrote: pyproject.toml
        """
    )


def test_initialize_update(hatch, helpers, temp_dir):
    project_name = 'My.App'
    description = 'foo'

    project_file = temp_dir / 'pyproject.toml'
    project_file.write_text(
        """\
[build-system]
req = ["hatchling"]
build-backend = "build"

[project]
name = ""
description = ""
readme = "README.md"
requires-python = ">=3.8"
license = "MIT"
dynamic = ["version"]

[tool.hatch.version]
path = "o/__init__.py"
"""
    )

    with temp_dir.as_cwd():
        result = hatch('new', '--init', input=f'{project_name}\n{description}')

    assert result.exit_code == 0, result.output
    assert remove_trailing_spaces(result.output) == helpers.dedent(
        f"""
        Project name: {project_name}
        Description []: {description}

        Updated: pyproject.toml
        """
    )
    assert len(list(temp_dir.iterdir())) == 1
    assert project_file.read_text() == (
        f"""\
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-app"
description = "{description}"
readme = "README.md"
requires-python = ">=3.8"
license = "MIT"
dynamic = ["version"]

[tool.hatch.version]
path = "my_app/__init__.py"
"""
    )
