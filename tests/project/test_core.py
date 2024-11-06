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


class TestRawConfig:
    def test_missing(self, temp_dir):
        project = Project(temp_dir)
        project.find_project_root()

        assert project.raw_config == {'project': {'name': temp_dir.name}}

    def test_exists(self, temp_dir):
        project_file = temp_dir / 'pyproject.toml'
        project_file.touch()
        project = Project(temp_dir)
        project.find_project_root()

        config = {'project': {'name': 'foo'}, 'bar': 'baz'}
        project.save_config(config)

        assert project.raw_config == config

    def test_exists_without_project_table(self, temp_dir):
        project_file = temp_dir / 'pyproject.toml'
        project_file.touch()
        project = Project(temp_dir)
        project.find_project_root()

        assert project.raw_config == {'project': {'name': temp_dir.name}}


class TestEnsureCWD:
    def test_location_is_file(self, temp_dir, mocker):
        script_path = temp_dir / 'script.py'
        script_path.touch()
        project = Project(script_path)
        project.find_project_root()

        with temp_dir.as_cwd():
            mocker.patch('hatch.utils.fs.Path.as_cwd', side_effect=Exception)
            with project.ensure_cwd() as cwd:
                assert cwd == temp_dir

    def test_cwd_is_location(self, temp_dir, mocker):
        project_file = temp_dir / 'pyproject.toml'
        project_file.touch()
        project = Project(temp_dir)
        project.find_project_root()

        with temp_dir.as_cwd():
            mocker.patch('hatch.utils.fs.Path.as_cwd', side_effect=Exception)
            with project.ensure_cwd() as cwd:
                assert cwd == temp_dir

    def test_cwd_inside_location(self, temp_dir, mocker):
        project_file = temp_dir / 'pyproject.toml'
        project_file.touch()
        project = Project(temp_dir)
        project.find_project_root()

        subdir = temp_dir / 'subdir'
        subdir.mkdir()

        with subdir.as_cwd():
            mocker.patch('hatch.utils.fs.Path.as_cwd', side_effect=Exception)
            with project.ensure_cwd() as cwd:
                assert cwd == subdir

    def test_cwd_outside_location(self, temp_dir):
        subdir = temp_dir / 'subdir'
        subdir.mkdir()
        project_file = subdir / 'pyproject.toml'
        project_file.touch()
        project = Project(subdir)
        project.find_project_root()

        with temp_dir.as_cwd(), project.ensure_cwd() as cwd:
            assert cwd == subdir
