import os
from collections import OrderedDict

from sortedcontainers import SortedDict

from hatch.create import create_package
from hatch.project import Project
from hatch.settings import copy_default_settings
from hatch.utils import temp_chdir


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
        assert project.setup_user_section_error is None

        faulty_setup_contents = (
            '#################### Maintained by Hatch ###################\n'
            '########### BEGIN USER OVERRIDES #######\n'
        )

        with open(os.path.join(d, 'setup.py'), 'w') as f:
            f.write(faulty_setup_contents)
        new_project = Project(project_file)
        assert new_project.setup_user_section_error is not None


def test_project_class_empty_file():
    project = Project('non-existent-file')
    assert project.name is None
    assert project.description is None
    assert project.author is None
    assert project.author_email is None
    assert project.user_defined is ''
    assert project.url is None
    assert project.license is None
    assert project.version is None
    assert project.packages == SortedDict()
    assert project.commands == OrderedDict()


def test_project_structure():
    project = Project('non-existent-file')
    project_structure = project.structure()
    assert 'metadata' in project_structure
    assert 'packages' in project_structure
    assert 'dev-packages' in project_structure
    assert 'tool' in project_structure
    assert 'commands' in project_structure['tool']['hatch']


def test_project_user_section_error():
    project = Project('non-existent-file')
    project_structure = project.structure()
    assert 'metadata' in project_structure
    assert 'packages' in project_structure
    assert 'dev-packages' in project_structure
    assert 'tool' in project_structure
    assert 'commands' in project_structure['tool']['hatch']


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
