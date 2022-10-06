import pytest

from hatch.project.core import Project


def read_readme(project_dir):
    return repr((project_dir / 'README.txt').read_text())[1:-1]


@pytest.fixture(autouse=True)
def local_builder(mock_backend_process, mocker):
    if mock_backend_process:
        mocker.patch('hatch.env.virtual.VirtualEnvironment.build_environment')

    yield


class TestBuildDependenciesInstalled:
    def test_default_all(self, hatch, temp_dir, helpers):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)
            assert result.exit_code == 0, result.output

        path = temp_dir / 'my-app'

        (path / 'README.md').replace(path / 'README.txt')

        project = Project(path)
        config = dict(project.raw_config)
        config['project']['readme'] = 'README.txt'
        project.save_config(config)

        with path.as_cwd():
            result = hatch('project', 'metadata')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            {{
                "name": "my-app",
                "version": "0.0.1",
                "readme": {{
                    "content-type": "text/plain",
                    "text": "{read_readme(path)}"
                }},
                "requires-python": ">=3.7",
                "license": "MIT",
                "authors": [
                    {{
                        "name": "Foo Bar",
                        "email": "foo@bar.baz"
                    }}
                ],
                "classifiers": [
                    "Development Status :: 4 - Beta",
                    "Programming Language :: Python",
                    "Programming Language :: Python :: 3.7",
                    "Programming Language :: Python :: 3.8",
                    "Programming Language :: Python :: 3.9",
                    "Programming Language :: Python :: 3.10",
                    "Programming Language :: Python :: 3.11",
                    "Programming Language :: Python :: Implementation :: CPython",
                    "Programming Language :: Python :: Implementation :: PyPy"
                ],
                "urls": {{
                    "Documentation": "https://github.com/unknown/my-app#readme",
                    "Issues": "https://github.com/unknown/my-app/issues",
                    "Source": "https://github.com/unknown/my-app"
                }}
            }}
            """
        )

    def test_field_readme(self, hatch, temp_dir):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)
            assert result.exit_code == 0, result.output

        path = temp_dir / 'my-app'

        (path / 'README.md').replace(path / 'README.txt')

        project = Project(path)
        config = dict(project.raw_config)
        config['project']['readme'] = 'README.txt'
        project.save_config(config)

        with path.as_cwd():
            result = hatch('project', 'metadata', 'readme')

        assert result.exit_code == 0, result.output
        assert result.output == (
            f"""\
{(path / 'README.txt').read_text()}
"""
        )

    def test_field_string(self, hatch, temp_dir, helpers):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)
            assert result.exit_code == 0, result.output

        path = temp_dir / 'my-app'

        with path.as_cwd():
            result = hatch('project', 'metadata', 'license')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            """
            MIT
            """
        )

    def test_field_complex(self, hatch, temp_dir, helpers):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)
            assert result.exit_code == 0, result.output

        path = temp_dir / 'my-app'

        with path.as_cwd():
            result = hatch('project', 'metadata', 'urls')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            """
            {
                "Documentation": "https://github.com/unknown/my-app#readme",
                "Issues": "https://github.com/unknown/my-app/issues",
                "Source": "https://github.com/unknown/my-app"
            }
            """
        )


class TestBuildDependenciesMissing:
    @pytest.mark.allow_backend_process
    def test_incompatible_environment(self, hatch, temp_dir, helpers):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)
            assert result.exit_code == 0, result.output

        path = temp_dir / 'my-app'

        project = Project(path)
        config = dict(project.raw_config)
        config['build-system']['requires'].append('foo')
        project.save_config(config)
        helpers.update_project_environment(
            project, 'default', {'skip-install': True, 'python': '9000', **project.config.envs['default']}
        )

        with path.as_cwd():
            result = hatch('project', 'metadata')

        assert result.exit_code == 1, result.output
        assert result.output == helpers.dedent(
            """
            Environment `default` is incompatible: cannot locate Python: 9000
            """
        )

    def test_default_all(self, hatch, temp_dir, helpers):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)
            assert result.exit_code == 0, result.output

        path = temp_dir / 'my-app'

        (path / 'README.md').replace(path / 'README.txt')

        project = Project(path)
        config = dict(project.raw_config)
        config['build-system']['requires'].append('foo')
        config['project']['readme'] = 'README.txt'
        project.save_config(config)

        with path.as_cwd():
            result = hatch('project', 'metadata')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            Setting up build environment for missing dependencies
            {{
                "name": "my-app",
                "version": "0.0.1",
                "readme": {{
                    "content-type": "text/plain",
                    "text": "{read_readme(path)}"
                }},
                "requires-python": ">=3.7",
                "license": "MIT",
                "authors": [
                    {{
                        "name": "Foo Bar",
                        "email": "foo@bar.baz"
                    }}
                ],
                "classifiers": [
                    "Development Status :: 4 - Beta",
                    "Programming Language :: Python",
                    "Programming Language :: Python :: 3.7",
                    "Programming Language :: Python :: 3.8",
                    "Programming Language :: Python :: 3.9",
                    "Programming Language :: Python :: 3.10",
                    "Programming Language :: Python :: 3.11",
                    "Programming Language :: Python :: Implementation :: CPython",
                    "Programming Language :: Python :: Implementation :: PyPy"
                ],
                "urls": {{
                    "Documentation": "https://github.com/unknown/my-app#readme",
                    "Issues": "https://github.com/unknown/my-app/issues",
                    "Source": "https://github.com/unknown/my-app"
                }}
            }}
            """
        )

    def test_field_readme(self, hatch, temp_dir):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)
            assert result.exit_code == 0, result.output

        path = temp_dir / 'my-app'

        (path / 'README.md').replace(path / 'README.txt')

        project = Project(path)
        config = dict(project.raw_config)
        config['build-system']['requires'].append('foo')
        config['project']['readme'] = 'README.txt'
        project.save_config(config)

        with path.as_cwd():
            result = hatch('project', 'metadata', 'readme')

        assert result.exit_code == 0, result.output
        assert result.output == (
            f"""\
Setting up build environment for missing dependencies
{(path / 'README.txt').read_text()}
"""
        )

    def test_field_string(self, hatch, temp_dir, helpers):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)
            assert result.exit_code == 0, result.output

        path = temp_dir / 'my-app'

        project = Project(path)
        config = dict(project.raw_config)
        config['build-system']['requires'].append('foo')
        project.save_config(config)

        with path.as_cwd():
            result = hatch('project', 'metadata', 'license')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            """
            Setting up build environment for missing dependencies
            MIT
            """
        )

    def test_field_complex(self, hatch, temp_dir, helpers):
        project_name = 'My.App'

        with temp_dir.as_cwd():
            result = hatch('new', project_name)
            assert result.exit_code == 0, result.output

        path = temp_dir / 'my-app'

        project = Project(path)
        config = dict(project.raw_config)
        config['build-system']['requires'].append('foo')
        project.save_config(config)

        with path.as_cwd():
            result = hatch('project', 'metadata', 'urls')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            """
            Setting up build environment for missing dependencies
            {
                "Documentation": "https://github.com/unknown/my-app#readme",
                "Issues": "https://github.com/unknown/my-app/issues",
                "Source": "https://github.com/unknown/my-app"
            }
            """
        )
