import pytest

from hatch.project.core import Project


class TestFindProjectRoot:
    def test_no_project(self, temp_dir):
        project = Project(temp_dir)
        assert project.find_project_root() is None

    @pytest.mark.parametrize('file_name', ['pyproject.toml', 'setup.py'])
    def test_direct(self, temp_dir, file_name):
        project = Project(temp_dir)

        project_file = temp_dir / file_name
        project_file.touch()

        assert project.find_project_root() == temp_dir

    @pytest.mark.parametrize('file_name', ['pyproject.toml', 'setup.py'])
    def test_recurse(self, temp_dir, file_name):
        project = Project(temp_dir)

        project_file = temp_dir / file_name
        project_file.touch()

        path = temp_dir / 'test'
        path.mkdir()

        assert project.find_project_root() == temp_dir

    @pytest.mark.parametrize('file_name', ['pyproject.toml', 'setup.py'])
    def test_no_path(self, temp_dir, file_name):
        project_file = temp_dir / file_name
        project_file.touch()

        path = temp_dir / 'test'
        project = Project(path)

        assert project.find_project_root() == temp_dir


class TestLoadProjectFromConfig:
    def test_no_project_no_project_dirs(self, config_file):
        assert Project.from_config(config_file.model, 'foo') is None

    def test_project_empty_string(self, config_file, temp_dir):
        config_file.model.projects[''] = str(temp_dir)
        assert Project.from_config(config_file.model, '') is None

    def test_project_basic_string(self, config_file, temp_dir):
        config_file.model.projects = {'foo': str(temp_dir)}
        project = Project.from_config(config_file.model, 'foo')
        assert project.chosen_name == 'foo'
        assert project.location == temp_dir

    def test_project_complex(self, config_file, temp_dir):
        config_file.model.projects = {'foo': {'location': str(temp_dir)}}
        project = Project.from_config(config_file.model, 'foo')
        assert project.chosen_name == 'foo'
        assert project.location == temp_dir

    def test_project_complex_null_location(self, config_file):
        config_file.model.projects = {'foo': {'location': ''}}
        assert Project.from_config(config_file.model, 'foo') is None

    def test_project_dirs(self, config_file, temp_dir):
        path = temp_dir / 'foo'
        path.mkdir()
        config_file.model.dirs.project = [str(temp_dir)]
        project = Project.from_config(config_file.model, 'foo')
        assert project.chosen_name == 'foo'
        assert project.location == path

    def test_project_dirs_null_dir(self, config_file):
        config_file.model.dirs.project = ['']
        assert Project.from_config(config_file.model, 'foo') is None

    def test_project_dirs_not_directory(self, config_file, temp_dir):
        path = temp_dir / 'foo'
        path.touch()
        config_file.model.dirs.project = [str(temp_dir)]
        assert Project.from_config(config_file.model, 'foo') is None


class TestChosenName:
    def test_selected(self, temp_dir):
        project = Project(temp_dir, name='foo')
        assert project.chosen_name == 'foo'

    def test_cwd(self, temp_dir):
        project = Project(temp_dir)
        assert project.chosen_name is None


class TestLocation:
    def test_no_project(self, temp_dir):
        project = Project(temp_dir)
        assert project.location == temp_dir
        assert project.root is None

    @pytest.mark.parametrize('file_name', ['pyproject.toml', 'setup.py'])
    def test_project(self, temp_dir, file_name):
        project_file = temp_dir / file_name
        project_file.touch()

        project = Project(temp_dir)
        assert project.location == temp_dir
        assert project.root == temp_dir
