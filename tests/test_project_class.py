import os

from hatch.create import create_package
from hatch.settings import copy_default_settings
from hatch.utils import temp_chdir
from hatch.project import Project
from sortedcontainers import SortedDict


def test_project_class():
    with temp_chdir() as d:
        settings = copy_default_settings()
        settings['name'] = 'Don Quixote'
        settings['description'] = 'Project description.'
        settings['email'] = 'don@quixote.xyz'
        create_package(d, 'ok', settings)

        project_file = os.path.join(d, 'pyproject.toml')
        project = Project(project_file)
        assert project.name == 'ok'
        assert project.description == 'Project description.'
        assert project.author == 'Don Quixote'
        assert project.author_email == 'don@quixote.xyz'
        assert project.user_defined == '\n'
        assert project.url == 'https://github.com/_/ok'
        assert project.license == 'MIT/Apache-2.0'
        assert project.version == '0.0.1'
        assert project.packages == SortedDict()
        assert project.commands == {'prerelease': 'hatch build'}

def test_project_class_version_setter():
    with temp_chdir() as d:
        settings = copy_default_settings()
        create_package(d, 'ok', settings)

        project_file = os.path.join(d, 'pyproject.toml')
        project = Project(project_file)
        project.version = '0.5.0'
        assert project.version == '0.5.0'

def test_project_class_add_package():
    with temp_chdir() as d:
        settings = copy_default_settings()
        create_package(d, 'ok', settings)

        project_file = os.path.join(d, 'pyproject.toml')
        project = Project(project_file)
        project.add_package('requests', '>=1.9.0')
        project.add_package('pytest', '>=1.5.0', dev=True)
        assert project.packages == {'requests': '>=1.9.0'}
        assert project.dev_packages == {'pytest': '>=1.5.0'}
