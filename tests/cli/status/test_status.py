import pytest

from hatch.config.constants import ConfigEnvVars
from hatch.utils.fs import temp_chdir
from hatch.utils.structures import EnvVars


class TestModeLocalDefault:
    def test_no_project(self, hatch, isolation, config_file, helpers):
        result = hatch('status')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            [Project] - <no project detected>
            [Location] - {isolation}
            [Config] - {config_file.path}
            """
        )

    def test_found_project(self, hatch, temp_dir, config_file, helpers):
        project_file = temp_dir / 'pyproject.toml'
        project_file.touch()

        with temp_dir.as_cwd():
            result = hatch('status')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            [Project] - {temp_dir.name} (current directory)
            [Location] - {temp_dir}
            [Config] - {config_file.path}
            """
        )


class TestProjectExplicit:
    @pytest.mark.parametrize('file_name', ['pyproject.toml', 'setup.py'])
    def test_found_project_flag(self, hatch, temp_dir, config_file, helpers, file_name):
        project_file = temp_dir / file_name
        project_file.touch()

        project = 'foo'
        config_file.model.projects = {project: str(temp_dir)}
        config_file.save()

        result = hatch('-p', project, 'status')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            [Project] - {project}
            [Location] - {temp_dir}
            [Config] - {config_file.path}
            """
        )

    @pytest.mark.parametrize('file_name', ['pyproject.toml', 'setup.py'])
    def test_found_project_env(self, hatch, temp_dir, config_file, helpers, file_name):
        project_file = temp_dir / file_name
        project_file.touch()

        project = 'foo'
        config_file.model.projects = {project: str(temp_dir)}
        config_file.save()

        with EnvVars({ConfigEnvVars.PROJECT: project}):
            result = hatch('status')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            [Project] - {project}
            [Location] - {temp_dir}
            [Config] - {config_file.path}
            """
        )

    def test_unknown_project(self, hatch):
        project = 'foo'
        result = hatch('-p', project, 'status')

        assert result.exit_code == 1
        assert result.output == f'Unable to locate project {project}\n'

    def test_not_a_project(self, hatch, temp_dir, config_file):
        project = 'foo'
        config_file.model.project = project
        config_file.model.projects = {project: str(temp_dir)}
        config_file.save()

        result = hatch('-p', project, 'status')

        assert result.exit_code == 1
        assert result.output == f'Unable to locate project {project}\n'


class TestModeProject:
    def test_no_project(self, hatch, isolation, config_file, helpers):
        config_file.model.mode = 'project'
        config_file.save()

        result = hatch('status')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            Mode is set to `project` but no project is set, defaulting to the current directory
            [Project] - <no project detected>
            [Location] - {isolation}
            [Config] - {config_file.path}
            """
        )

    def test_unknown_project(self, hatch, isolation, config_file, helpers):
        project = 'foo'
        config_file.model.mode = 'project'
        config_file.model.project = project
        config_file.save()

        result = hatch('status')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            Unable to locate project {project}, defaulting to the current directory
            [Project] - <no project detected>
            [Location] - {isolation}
            [Config] - {config_file.path}
            """
        )

    def test_not_a_project(self, hatch, temp_dir, config_file, helpers):
        project = 'foo'
        config_file.model.mode = 'project'
        config_file.model.project = project
        config_file.model.projects = {project: str(temp_dir)}
        config_file.save()

        result = hatch('status')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            [Project] - {project} (not a project)
            [Location] - {temp_dir}
            [Config] - {config_file.path}
            """
        )

    @pytest.mark.parametrize('file_name', ['pyproject.toml', 'setup.py'])
    def test_found_project(self, hatch, temp_dir, config_file, helpers, file_name):
        project_file = temp_dir / file_name
        project_file.touch()

        project = 'foo'
        config_file.model.mode = 'project'
        config_file.model.project = project
        config_file.model.projects = {project: str(temp_dir)}
        config_file.save()

        result = hatch('status')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            [Project] - {project}
            [Location] - {temp_dir}
            [Config] - {config_file.path}
            """
        )


class TestModeAware:
    def test_no_detection_no_project(self, hatch, config_file, helpers, isolation):
        config_file.model.mode = 'aware'
        config_file.save()

        result = hatch('status')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            Mode is set to `aware` but no project is set, defaulting to the current directory
            [Project] - <no project detected>
            [Location] - {isolation}
            [Config] - {config_file.path}
            """
        )

    def test_unknown_project(self, hatch, isolation, config_file, helpers):
        project = 'foo'
        config_file.model.project = project
        config_file.model.mode = 'aware'
        config_file.save()

        result = hatch('status')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            Unable to locate project {project}, defaulting to the current directory
            [Project] - <no project detected>
            [Location] - {isolation}
            [Config] - {config_file.path}
            """
        )

    def test_not_a_project(self, hatch, temp_dir, config_file, helpers):
        project = 'foo'
        config_file.model.project = project
        config_file.model.projects = {project: str(temp_dir)}
        config_file.model.mode = 'aware'
        config_file.save()

        result = hatch('status')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            [Project] - {project} (not a project)
            [Location] - {temp_dir}
            [Config] - {config_file.path}
            """
        )

    @pytest.mark.parametrize('file_name', ['pyproject.toml', 'setup.py'])
    def test_found_project(self, hatch, temp_dir, config_file, helpers, file_name):
        project_file = temp_dir / file_name
        project_file.touch()

        project = 'foo'
        config_file.model.project = project
        config_file.model.projects = {project: str(temp_dir)}
        config_file.model.mode = 'aware'
        config_file.save()

        result = hatch('status')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            [Project] - {project}
            [Location] - {temp_dir}
            [Config] - {config_file.path}
            """
        )

    def test_local_override(self, hatch, temp_dir, config_file, helpers):
        project_file = temp_dir / 'pyproject.toml'
        project_file.touch()

        project = 'foo'
        config_file.model.project = project
        config_file.model.projects = {project: str(temp_dir)}
        config_file.model.mode = 'aware'
        config_file.save()

        with temp_chdir() as d:
            d.joinpath('pyproject.toml').touch()
            result = hatch('status')

        assert result.exit_code == 0, result.output
        assert result.output == helpers.dedent(
            f"""
            [Project] - {d.name} (current directory)
            [Location] - {d}
            [Config] - {config_file.path}
            """
        )
